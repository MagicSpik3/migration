import unittest
import subprocess
import json
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.utils.ollama_client import get_ollama_response
from src.converter.prompts import VALUE_LABEL_TEMPLATE, SYSTEM_PROMPT
from src.utils.spss_parser import parse_spss_value_labels

# Paths
R_PROBE_SCRIPT = "tests/verification/r_probe.R"
TEMP_JSON = "tests/verification/r_output_temp.json"

# --- CONFIGURATION ---
# Point this to your actual R package location
R_PKG_PATH = "/home/jonny/git/weekly_deaths_rap/weekly.deaths" 

class TestConfigEquivalence(unittest.TestCase):

    def test_factor_levels_equivalence(self):
        function_name = "create_factor_levels"
        
        # --- 1. Get the "Truth" from R ---
        print(f"\n--- Probing R: {function_name} ---")
        
        # Pass the package path as the 3rd argument
        cmd = ["Rscript", R_PROBE_SCRIPT, function_name, TEMP_JSON, R_PKG_PATH]
        
        # Capture BOTH stdout and stderr to debug crashes
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Print stdout too, as R sometimes prints errors there
            error_msg = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            self.fail(f"R execution failed:\n{error_msg}")
            
        with open(TEMP_JSON, 'r') as f:
            r_truth = json.load(f)
            
        if os.path.exists(TEMP_JSON):
            os.remove(TEMP_JSON)

        # --- 2. Get the Candidate from LLM ---
        # (Ideally load this from your crawler output, but hardcoded for verification test)
        r_source_code = """
        create_factor_levels <- function() {
          list(
            agegrp_5yr = c(
              "All ages", "Under 1", "1 to 4", "5 to 9", "10 to 14", "15 to 19",
              "20 to 24", "25 to 29", "30 to 34", "35 to 39", "40 to 44", "45 to 49",
              "50 to 54", "55 to 59", "60 to 64", "65 to 69", "70 to 74", "75 to 79",
              "80 to 84", "85 to 89", "90 to 94", "95 to 99", "100 and over"),
            sex = c("All people", "Female", "Male"),
            region = c("North East", "North West", "Yorkshire and The Humber", "East Midlands",
                       "West Midlands", "East of England", "London", "South East", "South West")
          )
        }
        """
        
       
        print(f"--- Asking LLM to convert ---")
        prompt = VALUE_LABEL_TEMPLATE.format(system_prompt=SYSTEM_PROMPT, r_code=r_source_code)
        spss_code = get_ollama_response(prompt)
        
        # --- DEBUG: PRINT THE OUTPUT ---
        print(f"\n[DEBUG] LLM Generated Output:\n{spss_code}\n-----------------------------")

        # --- 3. Parse SPSS Output ---
        spss_map = parse_spss_value_labels(spss_code)
        
       
        # --- 4. Compare ---
        print("--- Verifying Equivalence ---")
        # Just check the keys we included in the source code above
        check_vars = ["sex", "region", "agegrp_5yr"] 
        
        for var in check_vars:
            if var not in spss_map:
                self.fail(f"Variable '{var}' missing from SPSS output.")
            
            if var not in r_truth:
                self.fail(f"Variable '{var}' missing from R output (Truth).")

            r_values = r_truth[var]
            spss_values = spss_map[var]
            
            # Check length match
            self.assertEqual(len(r_values), len(spss_values), f"Length mismatch for {var}")
            
            # Check exact value match
            for val_idx, label_text in spss_values.items():
                # R list index is 0-based in Python List, but SPSS is 1-based Value
                expected_label = r_values[val_idx - 1]
                self.assertEqual(label_text, expected_label, 
                                 f"Mismatch in {var} value {val_idx}")

        print("✅ Equivalence Proven: R Truth matches SPSS Syntax.")

if __name__ == '__main__':
    unittest.main()