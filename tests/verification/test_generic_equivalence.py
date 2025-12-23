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

import unittest

class TestGenericEquivalence(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_csv = os.path.join(self.test_dir, "input_data.csv")
        self.r_output_json = os.path.join(self.test_dir, "r_output.json")
        self.spss_output_csv = os.path.join(self.test_dir, "spss_output.csv")
        self.spss_syntax_file = os.path.join(self.test_dir, "run.sps")

    @unittest.skip("Skipping Round-Trip Verification: PSPP generation is too brittle for now.")
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

            # 2. Generate Data & Run R (Same as before)
            print("2. Generating Data & Running R...")
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





            args_json_str = json.dumps(args_map)
            cmd = ["Rscript", R_PROBE_SCRIPT, TARGET_FUNCTION, args_json_str, self.r_output_json, R_PKG_PATH]
            subprocess.run(cmd, check=True) # Let it crash if R fails (we trust R probe now)
            
            with open(self.r_output_json, 'r') as f:
                r_data = json.load(f)
                df_r = pd.DataFrame(r_data) if isinstance(r_data, (list, dict)) else pd.DataFrame([r_data])
                r_csv_path = os.path.join(self.test_dir, "r_converted_truth.csv")
                df_r.to_csv(r_csv_path, index=False)

            # 3. DEFINE THE COMPILER CALLBACK
            # This function runs PSPP and tells the Agent if it worked.
            def validate_spss(code_candidate):
                # Create the full syntax wrapper (Import CSV + Candidate Code + Export)
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
                
                * --- CANDIDATE CODE START ---
                {code_candidate}
                * --- CANDIDATE CODE END ---
                
                SAVE TRANSLATE
                /OUTFILE='{self.spss_output_csv}'
                /TYPE=CSV
                /REPLACE.
                """
                
                with open(self.spss_syntax_file, 'w') as f:
                    f.write(full_syntax)
                
                # Run PSPP
                res = subprocess.run(['pspp', self.spss_syntax_file], capture_output=True, text=True)
                
                # Check success (Exit code 0 AND output file exists)
                if res.returncode == 0 and os.path.exists(self.spss_output_csv):
                    return True, ""
                else:
                    # Return the error message so the Agent can fix it
                    return False, f"PSPP Error:\n{res.stdout}\n{res.stderr}"

            # 4. Generate & Refine SPSS Syntax
            print("4. Generating & Refining SPSS Syntax...")
            
            # --- NEW: LOAD ROSETTA STONE ---
            rosetta_path = "spss_rosetta_stone.csv"
            if os.path.exists(rosetta_path):
                df_rosetta = pd.read_csv(rosetta_path)
                # Filter to only relevant columns to save token space
                mapping_table = df_rosetta[['r_function', 'spss_equivalent']].to_markdown(index=False)
                
                # Inject into the System Prompt
                enhanced_system_prompt = (
                    f"{SYSTEM_PROMPT}\n\n"
                    f"### APPROVED TRANSLATION TABLE (USE THESE MAPPINGS):\n"
                    f"{mapping_table}\n\n"
                    f"RULES:\n"
                    f"1. If an R function appears in the table above, you MUST use the provided SPSS Equivalent.\n"
                    f"2. Specifically for dates: Do NOT use DATE() or SUBSTR(). Use NUMBER(var, YMD8).\n"
                )
            else:
                print("[WARNING] Rosetta Stone CSV not found. Using default prompt.")
                enhanced_system_prompt = SYSTEM_PROMPT

            # Initialize Agent with the ENHANCED prompt
            agent = SPSSRefiningAgent(system_prompt=enhanced_system_prompt)
            
            conversion_request = f"Convert this R code to SPSS:\n\n{TARGET_SOURCE_CODE}"
            
            try:
                final_spss_code = agent.generate_and_refine(conversion_request, validate_spss)
                print(f"\n[DEBUG] Final Accepted Syntax:\n{'-'*40}\n{final_spss_code}\n{'-'*40}")
            except RuntimeError as e:
                self.fail(str(e))
                

            # 6. Compare
            print("6. Comparing Results...")
            match, msg = compare_outputs(r_csv_path, self.spss_output_csv)
            
            if match:
                print(f"✅ EQUIVALENCE VERIFIED for {TARGET_FUNCTION}")
            else:
                self.fail(f"Mismatch found: {msg}")



if __name__ == '__main__':
    unittest.main()