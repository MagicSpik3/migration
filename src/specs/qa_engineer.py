import os
import json
import subprocess
from src.utils.ollama_client import get_ollama_response

QA_PROMPT = """
You are a Lead QA Engineer.
Write a comprehensive `testthat` unit test file.

### RULES:

1. **Syntax:** Use `test_that("desc", {{ ... }})` and `expect_equal(act, exp)`.
2. **Mock Data:**
* Use strictly "YYYY-MM-DD" strings for dates.
* Use `date_death > date_reg` to ensure positive durations.

### SPECIFICATION:
{spec}
### R CODE TO TEST:

```r
{code}
```

### OUTPUT:

Only the R code. Start with `library(testthat)`.
"""

class QAEngineer:
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
        self.repo_root = os.path.dirname(os.path.dirname(self.manifest_path))


    def get_package_libs(self):
        """Reads DESCRIPTION file to find required libraries."""
        desc_path = os.path.join(self.repo_root, "DESCRIPTION")
        libs = {"testthat"} # Always required for testing
        
        if os.path.exists(desc_path):
            with open(desc_path, 'r') as f:
                content = f.read()
                # Very basic parser for "Imports:" block
                if "Imports:" in content:
                    block = content.split("Imports:")[1].split("Encoding:")[0]
                    # Clean up commas, newlines, and spaces
                    for item in block.replace("\n", "").replace(" ", "").split(","):
                        if item: libs.add(item)
        else:
            # Fallback defaults
            libs.update(["dplyr", "lubridate", "stringr", "readr"])
            
        return [f"library({lib})" for lib in sorted(list(libs))]







    def generate_tests(self, entry):
        func_name = entry['r_function_name']
        r_path = entry['r_file']
        spec_path = entry['spec_file']
        
        # Calculate paths
        # We assume r_file is in .../r_from_spec/filename.R
        # We want tests in .../tests/test_filename.R
        r_dir = os.path.dirname(r_path)
        base_dir = os.path.dirname(r_dir)
        test_dir = os.path.join(base_dir, "tests")
        
        os.makedirs(test_dir, exist_ok=True)
        test_path = os.path.join(test_dir, f"test_{func_name}.R")
        
        print(f"🧪 Generating QA Suite for {func_name}...")
        
        with open(r_path, 'r') as f: r_code = f.read()
        with open(spec_path, 'r') as f: spec_content = f.read()
        
        prompt = QA_PROMPT.format(spec=spec_content, code=r_code)
        response = get_ollama_response(prompt)
        # ... inside generate_tests ...
        # --- IMPROVED CLEANUP ---
        # 1. Strip Markdown Code Blocks
        if "```r" in response: 
            test_code = response.split("```r")[1].split("```")[0].strip()
        elif "```" in response: 
            test_code = response.split("```")[1].split("```")[0].strip()
        else: 
            test_code = response.strip()

        # 2. Aggressive Header Removal (Fixes "1. **Mock Data" error)
        # We drop everything before the first "library(" or "test_that("
        lines = test_code.splitlines()
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("library(") or line.strip().startswith("test_that(") or line.strip().startswith("source("):
                start_index = i
                break
        
        test_code = "\n".join(lines[start_index:])
        # ------------------------
        # Build Dynamic Header
        lib_calls = "\n".join(self.get_package_libs())
        header = f"{lib_calls}\n\nsource('{r_path}')\n\n"
        
        # Clean up any manual library calls from LLM
        clean_body = test_code
        for lib in ["testthat", "dplyr", "lubridate", "stringr", "readr"]:
            clean_body = clean_body.replace(f"library({lib})", "")
            
        with open(test_path, 'w') as f:
            f.write(header + clean_body.strip())
            
        return test_path


    def run_tests(self, test_path):
        cmd = ["Rscript", test_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        # Combine stdout and stderr, as testthat often prints to both
        full_output = res.stdout + "\n" + res.stderr
        
        # Filter out noisy library attachment lines
        clean_log = []
        for line in full_output.splitlines():
            if "Attaching package" in line: continue
            if "The following objects are masked" in line: continue
            if "library(" in line: continue
            if line.strip() == "": continue
            clean_log.append(line)
            
        if res.returncode == 0:
            print(f"   ✅ Tests PASSED.")
            return True
        else:
            print(f"   ❌ Tests FAILED.")
            print(f"   --- Error Log ---")
            # Print the first 20 lines of the CLEAN log
            print('\n'.join(clean_log[:20]))
            print("-------------------")
            return False



    def run(self):
        with open(self.manifest_path, 'r') as f: manifest = json.load(f)
        overall_success = True
        for entry in manifest:
            if entry.get('role') != 'controller' and os.path.exists(entry['r_file']):
                if not self.run_tests(self.generate_tests(entry)):
                    overall_success = False
        return overall_success

if __name__ == "__main__":
    QAEngineer().run()