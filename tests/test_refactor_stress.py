import unittest
import os
import subprocess
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestRefactorStress(unittest.TestCase):

    def setUp(self):
        self.test_dir = "temp_refactor_stress"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Locate the refactor script
        # Assumes running from root of repo
        self.refactor_script = os.path.abspath("src/utils/refactor.R")
        
        if not os.path.exists(self.refactor_script):
            self.skipTest(f"Refactor script not found at {self.refactor_script}")

    def run_refactor(self, r_file_path):
        """Helper to run the Rscript process."""
        cmd = ["Rscript", self.refactor_script, r_file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_challenge_nested_date_math(self):
        """Challenge: Nested Date Math inside cut().
        
        Input:  cut(date_death - date_reg, ...)
        
        Why it fails: 'date_death - date_reg' returns a 'difftime' object.
        'cut()' requires a numeric vector. The refactorer MUST wrap the subtraction 
        in 'as.numeric()' or the R code will crash at runtime.
        """
        
        # 1. The Toxic Code
        r_file = os.path.join(self.test_dir, "nested_math.R")
        code = """
        library(dplyr)
        
        process_data <- function(df) {
            df %>%
                mutate(
                    # DANGER: Subtraction returns difftime, cut() expects numeric
                    duration_group = cut(date_death - date_reg, breaks = c(0, 10, 30)),
                    
                    # DANGER: Simple subtraction often needs explicit casting for safety
                    simple_delay = date_death - date_reg
                )
        }
        """
        with open(r_file, 'w') as f:
            f.write(code)

        # 2. Run the Refactorer
        print(f"\n⚡ Running Refactorer on {r_file}...")
        res = self.run_refactor(r_file)
        
        if res.returncode != 0:
            print(f"❌ Refactorer Crashed:\n{res.stderr}")
            self.fail("Refactoring script crashed on nested logic.")

        # 3. Validation: Did it fix the logic?
        with open(r_file, 'r') as f:
            new_code = f.read()

        print(f"   [DEBUG] New Code:\n{new_code}")

        # It SHOULD have wrapped the math in as.numeric(...)
        self.assertIn("as.numeric", new_code, "Refactorer failed to inject type safety (as.numeric)!")
        
        # Specific check for the nested case
        # We expect: cut(as.numeric(difftime(date_death, date_reg, units="days")), ...)
        # OR at least: cut(as.numeric(date_death - date_reg), ...)
        self.assertTrue(
            "as.numeric(date_death - date_reg)" in new_code or "difftime" in new_code, 
            "Refactorer failed to fix the nested 'cut(a-b)' logic."
        )

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

if __name__ == "__main__":
    unittest.main()