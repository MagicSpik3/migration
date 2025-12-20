import subprocess
import os
import pandas as pd
from src.utils.validators import PSPPValidator # Reusing your validator logic
from tests.verification.comparator import compare_outputs

class VerificationRunner:
    def __init__(self, temp_dir="/tmp/migration_test"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def generate_spss_driver(self, csv_path, syntax_code):
        """
        Creates a full SPSS script that:
        1. Loads the CSV
        2. Runs the LLM-generated logic
        3. Saves the result to CSV
        """
        output_csv = os.path.join(self.temp_dir, "spss_output.csv")
        
        # We need a dynamic GET DATA command. 
        # For this prototype, we assume the CSV has a header.
        driver_script = f"""
        GET DATA /TYPE=TXT
          /FILE='{csv_path}'
          /ARRANGEMENT=DELIMITED
          /DELCASE=LINE
          /FIRSTCASE=2
          /DELIMITERS=",".
        
        * Run the Translated Logic.
        {syntax_code}
        
        * Export Result.
        SAVE TRANSLATE
          /OUTFILE='{output_csv}'
          /TYPE=CSV
          /REPLACE.
        """
        return driver_script, output_csv

    def run_test(self, r_script_path, spss_syntax, input_csv):
        # 1. Run R (Wrapper needed here to execute specific function)
        # For now, let's assume we have an 'r_output.csv' already for testing
        r_out_path = os.path.join(self.temp_dir, "r_output.csv")
        
        # ... logic to call Rscript would go here ...

        # 2. Run SPSS
        driver_code, spss_out_path = self.generate_spss_driver(input_csv, spss_syntax)
        
        # Use existing validator class to run the code
        # We save the driver to a file first
        driver_file = os.path.join(self.temp_dir, "run.sps")
        with open(driver_file, 'w') as f:
            f.write(driver_code)

        subprocess.run(['pspp', driver_file], capture_output=True)

        # 3. Compare
        success, msg = compare_outputs(r_out_path, spss_out_path)
        print(f"Verification Result: {msg}")

# Example Usage
if __name__ == "__main__":
    # You would plug this into your main loop later
    print("Verification harness ready.")