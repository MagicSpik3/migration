import os
import pandas as pd
import subprocess
import tempfile
import numpy as np

class RefactorVerifier:
    def __init__(self, r_v1_path, r_v2_path):
        self.r_v1 = r_v1_path
        self.r_v2 = r_v2_path
        self.work_dir = tempfile.mkdtemp()
        self.input_csv = os.path.join(self.work_dir, "input.csv")
        self.out_v1 = os.path.join(self.work_dir, "output_v1.csv")
        self.out_v2 = os.path.join(self.work_dir, "output_v2.csv")

    def generate_dummy_data(self):
        # Create dummy data matching the known schema (dor/dod as strings)
        df = pd.DataFrame({
            'dor': ["20230101", "20230520", "20221231"], 
            'dod': ["20230105", "20230525", "20221230"],
            # Add other columns if your script expects them, or make this generic later
        })
        df.to_csv(self.input_csv, index=False)
        print(f"   Generated dummy input at {self.input_csv}")


    def run_r_script(self, script_path, output_path):
            wrapper_code = f"""
            # Inject I/O
            if (!file.exists('{self.input_csv}')) stop("Input file not found")
            df <- read.csv('{self.input_csv}', colClasses = "character")
            
            # --- ORIGINAL LOGIC START ---
            {open(script_path).read()}
            # --- ORIGINAL LOGIC END ---
            
            write.csv(df, '{output_path}', row.names = FALSE)
            """
            
            wrapper_path = os.path.join(self.work_dir, "wrapper.R")
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_code)
                
            # CAPTURE OUTPUT for debugging
            result = subprocess.run(
                ["Rscript", wrapper_path], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print(f"\n[R Execution Error in {os.path.basename(script_path)}]")
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, result.args)


    def verify(self):
        print(f"--- Verifying Refactor ---")
        print(f"v1 (Ugly): {os.path.basename(self.r_v1)}")
        print(f"v2 (Clean): {os.path.basename(self.r_v2)}")
        
        self.generate_dummy_data()
        
        try:
            self.run_r_script(self.r_v1, self.out_v1)
            self.run_r_script(self.r_v2, self.out_v2)
        except subprocess.CalledProcessError as e:
            print(f"❌ Execution Failed: {e}")
            return False

        # Compare
        df1 = pd.read_csv(self.out_v1)
        df2 = pd.read_csv(self.out_v2)
        
        # Check equality (allowing for floating point minor diffs)
        try:
            pd.testing.assert_frame_equal(df1, df2, check_dtype=False)
            print("✅ SUCCESS: Refactored code preserves logic exactly.")
            return True
        except AssertionError as e:
            print("❌ FAILURE: Logic mismatch found.")
            print(e)
            return False

if __name__ == "__main__":
    # Point this to your actual files
    base = os.path.expanduser("~/git/dummy_spss_repo")
    v1 = os.path.join(base, "r_migrated/calc_delays.R")
    v2 = os.path.join(base, "r_refactored/calc_delays.R")
    
    verifier = RefactorVerifier(v1, v2)
    verifier.verify()