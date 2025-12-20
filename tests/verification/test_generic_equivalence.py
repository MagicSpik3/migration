import unittest
import subprocess
import json
import os
import sys
import pandas as pd
import tempfile
import re


# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.utils.ollama_client import get_ollama_response
from src.converter.prompts import DATA_INFERENCE_PROMPT, CANDIDATE_PROMPT_TEMPLATE, SYSTEM_PROMPT  # <--- Add this
from src.utils.data_factory import UniversalDataGenerator
from tests.verification.comparator import compare_outputs
# You may need to import your PSPP validator logic or replicate the wrapper here
# For simplicity, I'll inline a basic PSPP wrapper

# --- CONFIGURATION ---
R_PKG_PATH = "/home/jonny/git/weekly_deaths_rap/weekly.deaths"
R_PROBE_SCRIPT = "tests/verification/r_probe_generic.R"

# We'll pick one 'Logic' function to test first.
# 'registration_delays' is a good candidate if it takes a dataframe.

# OLD:
# TARGET_FUNCTION = "registration_delays"

# NEW:
TARGET_FUNCTION = "calc_registration_delays"

# Placeholder source code (In reality, you'd load this from your crawler JSON)
# For the test, copy the content of R/registration_delays.R here or load it.
TARGET_SOURCE_CODE = """
#' Calculate registration delays for death data
#'
#' @description Converts dor and reg_stat_dor to dates and
#' adds new column of the delay in days, throws an error if registration date
#' is before the occurrence date.
#'
#' @param data Data frame of all year death data.
#'
#' @return Data frame with additional delay column.
#' @export
#'
calc_registration_delays <- function(data) {

  data <- dplyr::mutate(
    data,
    dor = as.Date(as.character(dor), format = "%Y%m%d"),
    dod = as.Date(as.character(dod), format = "%Y%m%d"),
    delay_days = as.numeric(difftime(dor, dod, units = c("days")))
  )

  if (min(data$delay_days) < 0) {
    stop("A death registration date is before death occurence date")
  }

  data
}
"""


class TestGenericEquivalence(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_csv = os.path.join(self.test_dir, "input_data.csv")
        self.r_output_json = os.path.join(self.test_dir, "r_output.json")
        self.spss_output_csv = os.path.join(self.test_dir, "spss_output.csv")
        self.spss_syntax_file = os.path.join(self.test_dir, "run.sps")



    def test_end_to_end_equivalence(self):
            print(f"\n--- Testing Equivalence for: {TARGET_FUNCTION} ---")

            # 1. Infer Schema
            print("1. Inferring Data Schema...")
            schema_prompt = DATA_INFERENCE_PROMPT.format(r_code=TARGET_SOURCE_CODE)
            schema_json_str = get_ollama_response(schema_prompt)
            
            # Quick cleanup if LLM adds markdown
            if "```json" in schema_json_str:
                schema_json_str = schema_json_str.split("```json")[1].split("```")[0]
            
            try:
                schema = json.loads(schema_json_str)
                print("   Schema Inferred Successfully.")
            except json.JSONDecodeError:
                print(f"[DEBUG] Invalid JSON: {schema_json_str}")
                self.fail("LLM returned invalid JSON schema")

            # 2. Generate Data
            print("2. Generating Synthetic Data...")
            generator = UniversalDataGenerator(schema)
            inputs = generator.generate_inputs(rows=50)
            
            args_map = {}
            for arg_name, val in inputs.items():
                if isinstance(val, pd.DataFrame):
                    val.to_csv(self.input_csv, index=False)
                    args_map[arg_name] = self.input_csv
                    print(f"   Created CSV for argument '{arg_name}': {self.input_csv}")
                else:
                    args_map[arg_name] = val

            # 3. Run R Probe (Truth)
            print("3. Running R Probe...")
            args_json_str = json.dumps(args_map)
            cmd = ["Rscript", R_PROBE_SCRIPT, TARGET_FUNCTION, args_json_str, self.r_output_json, R_PKG_PATH]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.fail(f"R execution failed:\n{result.stderr}")
                
            # Convert R output to CSV for comparison
            with open(self.r_output_json, 'r') as f:
                r_data = json.load(f)
                df_r = pd.DataFrame(r_data) if isinstance(r_data, (list, dict)) else pd.DataFrame([r_data])
                r_csv_path = os.path.join(self.test_dir, "r_converted_truth.csv")
                df_r.to_csv(r_csv_path, index=False)

            # 4. Generate SPSS Syntax
            print("4. Generating SPSS Syntax...")
            spss_prompt = CANDIDATE_PROMPT_TEMPLATE.format(
                system_prompt=SYSTEM_PROMPT, 
                r_code=TARGET_SOURCE_CODE
            )
            spss_code = get_ollama_response(spss_prompt)
            
            print(f"\n[DEBUG] Generated SPSS Code:\n{'-'*40}\n{spss_code}\n{'-'*40}")

            # 5. Running SPSS...
            print("5. Running SPSS...")
            
            # --- DYNAMICALLY BUILD VARIABLE LIST ---
            # We read the CSV header to tell PSPP what variables to expect.
            # We default to A50 (String) for safety, letting the LLM convert them if needed.
            df_head = pd.read_csv(self.input_csv, nrows=1)
            var_list_syntax = "\n".join([f"    {col} A50" for col in df_head.columns])

            full_syntax = f"""
            GET DATA /TYPE=TXT
            /FILE='{self.input_csv}'
            /ARRANGEMENT=DELIMITED
            /DELCASE=LINE
            /FIRSTCASE=2
            /DELIMITERS=","
            /VARIABLES=
            {var_list_syntax}.
            
            * Run Translated Logic.
            {spss_code}
            
            SAVE TRANSLATE
            /OUTFILE='{self.spss_output_csv}'
            /TYPE=CSV
            /REPLACE.
            """
            
            with open(self.spss_syntax_file, 'w') as f:
                f.write(full_syntax)
                
            pspp_res = subprocess.run(['pspp', self.spss_syntax_file], capture_output=True, text=True)
            
            if pspp_res.returncode != 0 or not os.path.exists(self.spss_output_csv):
                print(f"\n[DEBUG] PSPP STDOUT:\n{pspp_res.stdout}")
                print(f"\n[DEBUG] PSPP STDERR:\n{pspp_res.stderr}")
                self.fail(f"PSPP Failed to generate output.")

            # 6. Compare
            print("6. Comparing Results...")
            match, msg = compare_outputs(r_csv_path, self.spss_output_csv)
            
            if match:
                print(f"✅ EQUIVALENCE VERIFIED for {TARGET_FUNCTION}")
            else:
                self.fail(f"Mismatch found: {msg}")



if __name__ == '__main__':
    unittest.main()