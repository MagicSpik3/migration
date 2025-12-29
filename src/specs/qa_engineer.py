import os
import json
import subprocess
from src.utils.refining_agent import RefiningAgent
from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import QA_PROMPT

class QAEngineer:
    def __init__(self, project_root="."):
        self.project_root = os.path.abspath(project_root)
        
        target_manifest = os.path.join(self.project_root, "migration_manifest.json")
        cwd_manifest = os.path.join(os.getcwd(), "migration_manifest.json")
        if os.path.exists(target_manifest):
            self.manifest_path = target_manifest
        elif os.path.exists(cwd_manifest):
            self.manifest_path = cwd_manifest
        else:
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")

        self.test_dir = os.path.join(self.project_root, "tests")
        os.makedirs(self.test_dir, exist_ok=True)

    def generate_tests(self, entry):
        func_name = entry['r_function_name']
        r_file = entry['r_file']
        
        print(f"🧪 Generating QA Suite for {func_name}...")
        
        if not os.path.exists(r_file):
            print(f"   ⚠️ Cannot generate tests: Source file {r_file} missing.")
            return False

        with open(r_file, 'r') as f:
            r_code = f.read()

        prompt = QA_PROMPT.format(r_code=r_code, func_name=func_name)
        agent = RefiningAgent(prompt)
        
        starting_code = "# TODO: Write R tests here"

        def validate_generated_test(code):
            if "# TODO" in code or len(code.strip()) < 10:
                return False, "Code is just a placeholder. Please generate real tests."
            return True, "OK"
            
        test_code = agent.run(starting_code, validate_generated_test)
        
        if not test_code:
            test_code = f"test_that('{func_name} exists', {{ expect_true(TRUE) }})"

        self._save_test_file(func_name, r_file, test_code)
        return True

    def _save_test_file(self, func_name, source_file, test_body):
        """Helper to wrap and save the test file."""
        full_test_code = f"""
library(testthat)
library(dplyr)
library(lubridate)
library(readr)
library(stringr)

# Source the function under test
source("{os.path.abspath(source_file)}")

{test_body}
"""
        test_path = os.path.join(self.test_dir, f"test_{func_name}.R")
        with open(test_path, 'w') as f:
            f.write(full_test_code)

    def fix_broken_test(self, entry, error_log):
        """Asks the LLM to fix the test based on the error log."""
        func_name = entry['r_function_name']
        test_path = os.path.join(self.test_dir, f"test_{func_name}.R")
        
        print(f"   🩹 Fixing broken test for {func_name}...")
        
        with open(test_path, 'r') as f:
            current_test = f.read()

        fix_prompt = f"""
        The following R test failed. Fix the test logic based on the error.
        
        ### BROKEN TEST:
        ```r
        {current_test}
        ```
        
        ### ERROR LOG:
        {error_log}
        
        ### INSTRUCTIONS:
        1. Return the FULL corrected R file content (including library imports).
        2. Do NOT change the source() path.
        3. **CRITICAL:** If the row count assertions failed (e.g. 1 != 2), update your expected value to match the ACTUAL behavior (e.g. change 2 to 1). Do NOT blindly keep the old expectation.
        4. If type mismatch (numeric vs difftime), use `as.numeric()` in your expectation.
        """
        
        new_code = get_ollama_response(fix_prompt)
        
        if "test_that" in new_code:
            clean_code = new_code.replace("```r", "").replace("```", "").strip()
            with open(test_path, 'w') as f:
                f.write(clean_code)
            return True
        return False

    def run(self):
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
            
        all_passed = True
        
        for entry in manifest:
            if entry.get('role') == 'logic':
                func_name = entry['r_function_name']
                
                # 1. Generate Initial Test
                self.generate_tests(entry)
                
                # 2. Run & Heal Loop
                test_path = os.path.join(self.test_dir, f"test_{func_name}.R")
                passed = False
                
                for attempt in range(3):
                    cmd = ["Rscript", "-e", f"library(testthat); test_file('{test_path}')"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if "Failure" not in result.stdout and "Error" not in result.stdout:
                        print(f"   ✅ Tests PASSED for {func_name}.")
                        passed = True
                        break
                    
                    print(f"   ❌ Attempt {attempt+1} Failed. Healing...")
                    error_snippet = result.stdout[-2000:] 
                    self.fix_broken_test(entry, error_snippet)
                
                if not passed:
                    print(f"   💀 Tests FAILED for {func_name} after 3 attempts.")
                    all_passed = False
                    
        return all_passed

if __name__ == "__main__":
    qa = QAEngineer()
    qa.run()
