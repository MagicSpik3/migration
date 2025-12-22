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
1. **Case Sensitivity:** (Keep existing...)
2. **Type Safety:** (Keep existing...)
3. **Naming & Side Effects:** (Keep existing...)

4. **Pipeline Continuity:** (Keep existing...)

5. **Boundary Completeness (CRITICAL):**
   - Check `case_when` logic for numeric gaps (Off-by-One errors).
   - ❌ GAP: `between(age, 18, 64)` then `age > 65` (Misses 65!)
   - ✅ FIXED: `between(age, 18, 64)` then `age >= 65`
   - Ensure the conditions cover the entire numeric range or provide a `.default`.

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
            Runs lintr with a pragmatic configuration for Migration:
            - Line Length: 120 chars (Modern standard)
            - Pipes: Allows %>%
            - Returns: Allows explicit return()
            - Globals: Allows dplyr column names
            - Assignment: Allows -> (Right assignment)
            """
            lint_cmd = (
                f"library(lintr); "
                f"custom_linters <- linters_with_defaults("
                f"  line_length_linter = line_length_linter(120), "
                f"  object_usage_linter = NULL, "
                f"  pipe_consistency_linter = NULL, "
                f"  return_linter = NULL, "
                f"  assignment_linter = NULL" 
                f"); "
                f"issues <- lint('{r_path}', linters = custom_linters); "
                f"print(issues); "
                f"cat(paste0('||COUNT||', length(issues)))"
            )

            cmd = ["Rscript", "-e", lint_cmd]
            
            try:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    print(f"   ⚠️  Lintr failed to run. (Error: {res.stderr.strip()})")
                    return 999
                
                output_parts = res.stdout.split("||COUNT||")
                report = output_parts[0].strip()
                count = int(output_parts[1].strip()) if len(output_parts) > 1 else 999
                
                if count > 0:
                    print(f"\n   --- Lintr Report for {os.path.basename(r_path)} ---")
                    print(report)
                    print("   -----------------------------------------------\n")
                    
                return count
            except Exception as e:
                print(f"   ⚠️  Lintr execution error: {e}")
                return 999



    def test_function(self, r_path, func_name):
            """Runs the micro-test with Enhanced Debugging."""
            wrapper_path = os.path.join(os.path.dirname(r_path), f"test_{func_name}.R")
            data_path = os.path.join(self.repo_root, "input_data.csv")
            
            if not os.path.exists(data_path):
                return f"FAIL: Data not found at {data_path}"

            r_script = f"""
            # Load the Full Tidyverse Suite
            suppressPackageStartupMessages(library(dplyr))
            suppressPackageStartupMessages(library(lubridate))
            suppressPackageStartupMessages(library(readr))
            
            # Enable traceback on error
            options(error = function() {{
                cat("\\n--- R TRACEBACK ---\\n")
                traceback()
                cat("--------------------\\n")
                quit(save = "no", status = 1)
            }})
            
            tryCatch({{
                source("{r_path}")
                
                # Load Data
                if(!file.exists("{data_path}")) stop("Input CSV missing")
                df <- read.csv("{data_path}", colClasses = "character")
                
                # Debug: Print schema before run
                # cat("DEBUG: Input Columns:", paste(names(df), collapse=", "), "\\n")
                
                # Execution
                res <- {func_name}(df)
                
                # Validation
                if(nrow(res) == 0) stop("Empty Result Dataframe")
                
                # Logic Check (Time Arrow)
                if("delay_days" %in% names(res)) {{
                    delays <- as.numeric(res$delay_days)
                    # Handle case where all delays might be NA
                    clean_delays <- na.omit(delays)
                    if(length(clean_delays) > 0 && any(clean_delays < 0)) {{
                        stop("Negative Delay Detected (Logic Inverted)")
                    }}
                }}
                
                cat("PASS")
            }}, error = function(e) {{
                cat("FAIL:", e$message)
                # We trigger the global error handler to get the traceback
                stop(e)
            }})
            """
            
            with open(wrapper_path, 'w') as f:
                f.write(r_script)
                
            try:
                # Capture both stdout and stderr
                res = subprocess.run(
                    ["Rscript", wrapper_path], 
                    capture_output=True, 
                    text=True
                )
                
                output = res.stdout.strip()
                
                # If R crashed or printed a FAIL message
                if res.returncode != 0 or "FAIL:" in output:
                    print(f"\n   🐛 DEBUG: Test Failed for {func_name}")
                    print(f"   🛑 Output: {output}")
                    print(f"   🛑 Errors: {res.stderr.strip()}")
                    
                    # Extract the failure message cleanly if possible
                    if "FAIL:" in output:
                        return output.split("FAIL:")[1].split("\n")[0].strip()
                    return "FAIL: R Runtime Error (See Debug Log)"
                    
                return "PASS"
                
            finally:
                # Cleanup only on success? No, let's keep it clean.
                # You can comment this out if you want to inspect 'test_func.R' manually
                if os.path.exists(wrapper_path): os.remove(wrapper_path)


    def auto_format_file(self, r_path):
            """
            Uses the R 'styler' package to mechanically fix whitespace and indentation.
            """
            cmd = ["Rscript", "-e", f"library(styler); style_file('{r_path}')"]
            subprocess.run(cmd, capture_output=True)



    def optimize_file(self, entry, force=False): # <--- Add force arg
            r_path = entry['r_file']
            func_name = entry['r_function_name']
            
            print(f"\n🔍 Assessing {func_name}...")
            self.save_vintage(r_path, func_name, "original")
            
            # 1. Pre-Check
            issues_before = self.check_lint_score(r_path)
            
            # LOGIC CHANGE: Only skip if NOT forced
            if issues_before == 0 and not force:
                print(f"   ✅ Code is clean. Skipping.")
                return

            if force:
                print(f"   💪 Force Mode Active. Optimizing despite {issues_before} issues...")
            else:
                print(f"   ⚠️  Found {issues_before} style issues. Optimizing...")


            # 2. Optimize (LLM Pass)
            with open(r_path, 'r') as f: original_code = f.read()
            prompt = OPTIMIZER_PROMPT.format(r_code=original_code)
            
            raw_response = get_ollama_response(prompt)
            
            # --- ROBUST EXTRACTION LOGIC ---
            clean_code = raw_response.strip()
            
            # Case A: Standard Markdown Code Blocks
            if "```r" in raw_response:
                clean_code = raw_response.split("```r")[1].split("```")[0].strip()
            elif "```R" in raw_response:
                clean_code = raw_response.split("```R")[1].split("```")[0].strip()
            elif "```" in raw_response:
                clean_code = raw_response.split("```")[1].split("```")[0].strip()
            
            # Case B: Fallback - If LLM just dumped text, ensure it looks like code
            # If it starts with "###" or "Here is", it's trash. We revert if we can't find code.
            if clean_code.startswith("###") or clean_code.startswith("Here is"):
                print("   ⚠️  LLM outputted conversational text without code blocks. Retrying extraction...")
                # Try to find the function definition start
                if f"{func_name} <- function" in raw_response:
                    start_index = raw_response.find(f"{func_name} <- function")
                    clean_code = raw_response[start_index:]
                    # Rough cut for end of file? Usually unnecessary if we catch the start.
                else:
                    print("   ❌ Parse Failed: Could not isolate R code.")
                    self.save_vintage(r_path, func_name, "parse_failed")
                    return # Abort optimization for this file
            
            # Save the Cleaned Candidate
            with open(r_path, 'w') as f: f.write(clean_code)

            # --- Mechanical Polish ---
            print("   🤖 Running 'styler' to fix whitespace...")
            self.auto_format_file(r_path)
            
            # 3. Test Functionality
            result = self.test_function(r_path, func_name)
            
            if result == "PASS":
                print(f"   ✅ Optimization SUCCESS.")
                self.save_vintage(r_path, func_name, "optimized_success")
                
                # 4. Final Quality Check
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


    def run(self, force_all=False): # <--- Add force_all arg
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            
            for entry in manifest:
                if entry.get('role') == 'controller': continue
                if not os.path.exists(entry['r_file']): continue
                
                # Pass the force flag down
                self.optimize_file(entry, force=force_all)


if __name__ == "__main__": 
    optimizer = CodeOptimizer()
    optimizer.run()                               