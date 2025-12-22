import os
import json
import subprocess
import shutil
import time
from src.utils.ollama_client import get_ollama_response


OPTIMIZER_PROMPT = """
You are a Senior R Developer. 
Refactor this code to be idiomatic `tidyverse` and FIX logical errors.

### RULES:
1. **No String Parsing:** Replace `substr`/`paste` with `lubridate::ymd()`.
2. **Fix Time Arrow Logic:** - We are calculating the delay between Death and Registration.
   - Registration happens AFTER Death.
   - ❌ WRONG: `date_death - date_reg` (Calculates negative days).
   - ✅ RIGHT: `date_reg - date_death` (Calculates positive delay).
   - **ACTION:** If you see the wrong order, SWAP IT.
3. **Safety:** - Use `as.numeric(difftime(date_reg, date_death, units="days"))`.
   - Ensure the function returns the dataframe.

### INPUT:
```r
{r_code}
OUTPUT:
Only the R code. """


class CodeOptimizer: 

    def __init__(self, manifest_path="migration_manifest.json"):
            # 1. Load the Manifest
            self.manifest_path = os.path.abspath(manifest_path)
            
            # Fallback: check if user is running from migration root but target is dummy_spss
            target_manifest = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
            
            # If the local manifest doesn't point to real files, switch to the target one
            if os.path.exists(target_manifest):
                self.manifest_path = target_manifest

            print(f"📍 Manifest active: {self.manifest_path}")

            # 2. Derive Repo Root from the Content
            with open(self.manifest_path, 'r') as f:
                data = json.load(f)
                # Grab the first R file listed
                # It will likely be: /home/jonny/git/dummy_spss_repo/r_from_spec/calc_delays.R
                first_r_file = data[0]['r_file']
                
                # If the path in JSON is relative, join it. If absolute, use it.
                if not os.path.isabs(first_r_file):
                    first_r_file = os.path.abspath(os.path.join(os.path.dirname(self.manifest_path), first_r_file))
                
                # The Repo Root is 2 levels up from 'r_from_spec/filename.R'
                # Level 1 up: .../dummy_spss_repo/r_from_spec
                # Level 2 up: .../dummy_spss_repo (This contains input_data.csv)
                self.repo_root = os.path.dirname(os.path.dirname(first_r_file))

            print(f"📍 Repo Root detected at: {self.repo_root}")
            
            # 3. Setup Snapshots
            self.snapshot_dir = os.path.join(self.repo_root, "snapshots")
            os.makedirs(self.snapshot_dir, exist_ok=True)


    def save_vintage(self, r_path, func_name, label):
        """Saves a copy of the code to snapshots/func/timestamp_label.R"""
        target_dir = os.path.join(self.snapshot_dir, func_name)
        os.makedirs(target_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"v{timestamp}_{label}.R"
        dest = os.path.join(target_dir, filename)
        shutil.copy(r_path, dest)
        return filename

    def check_lint_score(self, r_path):
        """
        Runs lintr with a permissive config (allows %>% and dplyr globals).
        """
        lint_cmd = (
            f"library(lintr); "
            # Disable object_usage (globals) and pipe_consistency (%>% vs |>)
            f"custom_linters <- linters_with_defaults("
            f"  object_usage_linter = NULL, "
            f"  pipe_consistency_linter = NULL"
            f"); "
            f"issues <- lint('{r_path}', linters = custom_linters); "
            f"print(issues); "
            f"cat(paste0('||COUNT||', length(issues)))"
        )

        cmd = ["Rscript", "-e", lint_cmd]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                return 999 # Lintr failed
            
            output_parts = res.stdout.split("||COUNT||")
            report = output_parts[0].strip()
            count = int(output_parts[1].strip()) if len(output_parts) > 1 else 999
            
            if count > 0:
                print(f"\n   --- Lintr Report for {os.path.basename(r_path)} ---")
                print(report)
                print("   -----------------------------------------------\n")
                
            return count
        except Exception:
            return 999

    def test_function(self, r_path, func_name):
        """Runs the micro-test."""
        wrapper_path = os.path.join(os.path.dirname(r_path), f"test_{func_name}.R")
        data_path = os.path.join(self.repo_root, "input_data.csv")
        
        # FINAL CHECK: Does data exist?
        if not os.path.exists(data_path):
            return f"FAIL: Data not found at {data_path}"

        r_script = f"""
        suppressPackageStartupMessages(library(dplyr))
        suppressPackageStartupMessages(library(lubridate))
        
        tryCatch({{
            source("{r_path}")
            
            df <- read.csv("{data_path}", colClasses = "character")
            res <- {func_name}(df)
            
            if(nrow(res) == 0) stop("Empty Result")
            if("delay_days" %in% names(res)) {{
                if(any(res$delay_days < 0)) stop("Negative Delay Detected (Logic Inverted)")
            }}
            cat("PASS")
        }}, error = function(e) {{
            cat("FAIL:", e$message)
        }})
        """
        
        with open(wrapper_path, 'w') as f:
            f.write(r_script)
            
        try:
            res = subprocess.run(["Rscript", wrapper_path], capture_output=True, text=True)
            return res.stdout.strip()
        finally:
            if os.path.exists(wrapper_path): os.remove(wrapper_path)



    def auto_format_file(self, r_path):
            """
            Uses the R 'styler' package to mechanically fix whitespace and indentation.
            """
            cmd = ["Rscript", "-e", f"library(styler); style_file('{r_path}')"]
            subprocess.run(cmd, capture_output=True)


    def optimize_file(self, entry):
            r_path = entry['r_file']
            func_name = entry['r_function_name']
            
            print(f"\n🔍 Assessing {func_name}...")
            self.save_vintage(r_path, func_name, "original")
            
            # 1. Pre-Check
            issues_before = self.check_lint_score(r_path)
            if issues_before == 0:
                print(f"   ✅ Code is clean. Skipping.")
                return

            print(f"   ⚠️  Found {issues_before} style issues. Optimizing...")


            # 2. Optimize (LLM Pass for Logic/Idioms)
            with open(r_path, 'r') as f: original_code = f.read()
            prompt = OPTIMIZER_PROMPT.format(r_code=original_code)
            new_code = get_ollama_response(prompt)
            # Clean markdown...
            if "```r" in new_code: new_code = new_code.split("```r")[1].split("```")[0]
            elif "```" in new_code: new_code = new_code.split("```")[1].split("```")[0]
            
            with open(r_path, 'w') as f: f.write(new_code.strip())

            # --- NEW STEP: Mechanical Polish ---
            print("   🤖 Running 'styler' to fix whitespace...")
            self.auto_format_file(r_path)
            # -----------------------------------

            # 3. Test Functionality
            result = self.test_function(r_path, func_name)
            
            if result == "PASS":
                print(f"   ✅ Optimization SUCCESS.")
                self.save_vintage(r_path, func_name, "optimized_success")
                
                # 4. Final Quality Check (The new step)
                print("   --- Final Quality Check ---")
                issues_after = self.check_lint_score(r_path)
                if issues_after == 0:
                    print(f"   ✨ PERFECT SCORE. All style issues resolved.")
                else:
                    print(f"   ⚠️  Code is functional, but {issues_after} style issues remain.")
            else:
                print(f"   ❌ Optimization FAILED: {result}")
                self.save_vintage(r_path, func_name, "optimized_failed")
                print(f"   ⏪ Reverting.")
                with open(r_path, 'w') as f: f.write(original_code)


    def run(self):
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        for entry in manifest:
            if entry.get('role') == 'controller': continue
            if not os.path.exists(entry['r_file']): continue
            self.optimize_file(entry)


if __name__ == "__main__": 
    optimizer = CodeOptimizer()
    optimizer.run()                               