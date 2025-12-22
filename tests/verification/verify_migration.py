import os
import sys

# --- FIX: Add Project Root to Path ---
# Get the directory where this script lives (tests/verification)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to get the Project Root (migration/)
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
# Add it to the system path so Python can find 'src'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- NOW imports will work ---
import pandas as pd
import subprocess
import tempfile
import shutil
# Import your custom reporter
from src.reporting.report_generator import VerificationReport

class MigrationVerifier:
    def __init__(self, spss_script, r_file):
        self.spss_script = spss_script
        self.r_file = r_file
        self.work_dir = tempfile.mkdtemp()
        self.input_csv = os.path.join(self.work_dir, "input_data.csv")
        self.spss_out = os.path.join(self.work_dir, "spss_output.csv")
        self.r_out = os.path.join(self.work_dir, "r_output.csv")

    def generate_data(self):
        # Create edge cases: Normal dates, End of year, Leap year
        df = pd.DataFrame({
            'dor': ["20230105", "20221231", "20240229", "20230520"],
            'dod': ["20230101", "20221225", "20240228", "20230510"]
        })
        df.to_csv(self.input_csv, index=False)
        print(f"   Generated test data at {self.input_csv}")

    def run_spss(self):
        with open(self.spss_script, 'r') as f:
            original_code = f.read()

        # REMOVE '/KEEP' to avoid syntax issues. Save everything.
        wrapper = f"""
        {original_code}
        
        SAVE TRANSLATE /OUTFILE='spss_output.csv' /TYPE=CSV /REPLACE.
        """
        
        with open(os.path.join(self.work_dir, "run.sps"), 'w') as f:
            f.write(wrapper)
            
        result = subprocess.run(
            ["pspp", "run.sps"], 
            cwd=self.work_dir, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print("\n[PSPP Execution Error]")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, result.args)

    def run_r(self):
        abs_r_file = os.path.abspath(self.r_file)
        
        wrapper_r = f"""
        source("{abs_r_file}")
        df <- read.csv("input_data.csv", colClasses = "character")
        result <- calc_delays(df)
        write.csv(result, "r_output.csv", row.names = FALSE)
        """
        
        with open(os.path.join(self.work_dir, "run.R"), 'w') as f:
            f.write(wrapper_r)
            
        result = subprocess.run(
            ["Rscript", "run.R"], 
            cwd=self.work_dir, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print("\n[R Execution Error]")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, result.args)
        
          

    def compare(self):
            print(f"\n--- Final Verification ---")
            self.generate_data()
            
            try:
                print("1. Running SPSS...")
                self.run_spss()
                print("2. Running R...")
                self.run_r()
                
                # --- FIX: Handle Headerless SPSS Output ---
                # Read SPSS file with header=None so the first row isn't eaten
                # sep=None allows Python to sniff for comma vs tab
                df_spss = pd.read_csv(self.spss_out, sep=None, engine='python', header=None)
                
                print(f"[DEBUG] SPSS Raw Columns: {len(df_spss.columns)} columns found")
                
                # We know the variable order from the SPSS script:
                # dor, dod, date_reg, date_death, delay_days
                # We map the ones we need for comparison:
                df_spss.rename(columns={
                    0: 'dor', 
                    1: 'dod', 
                    df_spss.columns[-1]: 'delay_days'
                }, inplace=True)
                
                # Read R Output (which has headers)
                df_r = pd.read_csv(self.r_out)
                df_r.columns = df_r.columns.str.lower().str.strip()

                print(f"[DEBUG] SPSS Mapped Cols: {list(df_spss.columns)}")
                print(f"[DEBUG] R Columns Found:  {list(df_r.columns)}")

                # Select and Compare only the input and output variables
                cols = ['dor', 'dod', 'delay_days']
                df_spss = df_spss[cols]
                df_r = df_r[cols]
                
                # Align types (Numeric)
                df_spss['delay_days'] = pd.to_numeric(df_spss['delay_days'])
                df_r['delay_days'] = pd.to_numeric(df_r['delay_days'])
                
                # Rounding to handle potentially different float precisions
                df_spss['delay_days'] = df_spss['delay_days'].round(0)
                df_r['delay_days'] = df_r['delay_days'].round(0)
              
                pd.testing.assert_frame_equal(df_spss, df_r, check_dtype=False)
                print("✅ MIGRATION SUCCESSFUL: R output matches SPSS exactly.")
                
                # --- NEW: Generate Certificate ---
                report = VerificationReport("calc_delays", self.spss_out, self.r_out)
                
                # Save report to the repo root for easy viewing
                report_path = os.path.expanduser("~/git/dummy_spss_repo/migration_certificate.html")
                report.generate_html(report_path)
            
                return True
                
            except subprocess.CalledProcessError:
                print("❌ Execution Failed")
                return False
            except KeyError as e:
                print(f"❌ MISSING COLUMN: {e}")
                return False
            except AssertionError as e:
                print("❌ DATA MISMATCH")
                print(e)
                return False
            finally:
                # Comment this out if you need to inspect the /tmp folder for debugging
                shutil.rmtree(self.work_dir)





if __name__ == "__main__":
    BASE = os.path.expanduser("~/git/dummy_spss_repo")
    SPSS_FILE = os.path.join(BASE, "syntax/calc_delays.sps")
    R_FILE = os.path.join(BASE, "r_from_spec/calc_delays.R")
    
    verifier = MigrationVerifier(SPSS_FILE, R_FILE)
    verifier.compare()