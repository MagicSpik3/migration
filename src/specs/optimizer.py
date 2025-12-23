import os
import json
import subprocess
import shutil
import time
import csv
from src.utils.ollama_client import get_ollama_response
from src.utils.refining_agent import RefiningAgent 

OPTIMIZER_PROMPT = """
You are a Senior R Developer. 
Refactor this code to be idiomatic `tidyverse` and FIX logical errors.

### RULES:
1. **Type Safety (CRITICAL):**
   - The input `df` is ALL CHARACTERS.
   - **CAST EVERYTHING:** `cut(as.numeric(age), ...)`
   - **CAST EVERYTHING:** `between(as.numeric(age), 18, 64)`

2. **Date Math (STRICT):**
   - ❌ WRONG: `as.numeric(d1 - d2, units="days")`
   - ✅ RIGHT: `as.numeric(difftime(d1, d2, units="days"))`
   - **Inherited Columns:** If `date_death` exists from step 1, DO NOT re-parse it with `ymd()`.

3. **Pipeline Continuity:**
   - If summarizing: `write.csv(summary_df, ...); return(df)`
   - Do NOT shadow function names (use `summary_df`, not `func_name`).

### INPUT:
```r
{r_code}
"""

class CodeOptimizer: 
    def __init__(self, manifest_path="migration_manifest.json"): 
        # 1. Load the Manifest 
        self.manifest_path = os.path.abspath(manifest_path)

        # Fallback: check if user is running from migration root but target is dummy_spss
        target_manifest = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
        
        # If the local manifest doesn't point to real files, switch to the target one
        if os.path.exists(target_manifest):
            self.manifest_path = target_manifest

        # 2. Derive Repo Root from the Content
        with open(self.manifest_path, 'r') as f:
            data = json.load(f)
            first_r_file = data[0]['r_file']
            
            if not os.path.isabs(first_r_file):
                first_r_file = os.path.abspath(os.path.join(os.path.dirname(self.manifest_path), first_r_file))
            
            self.repo_root = os.path.dirname(os.path.dirname(first_r_file))
        
        # 3. Setup Snapshots
        self.snapshot_dir = os.path.join(self.repo_root, "snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def generate_temp_schema(self):
        """Creates a temporary JSON schema from input_data.csv for the R Refactorer."""
        csv_path = os.path.join(self.repo_root, "input_data.csv")
        schema_path = os.path.join(self.repo_root, "temp_schema_types.json")
        
        if not os.path.exists(csv_path):
            return None
            
        try:
            # Simple heuristic: Read header and first row to guess types
            # In a real app, this would be more robust.
            # Here we just mark 'date_' columns as 'Date' for the Refactorer.
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
            schema = {}
            for col in headers:
                if "date" in col.lower() or "dob" in col.lower() or "dod" in col.lower() or "dor" in col.lower():
                    schema[col] = "Date"
                else:
                    schema[col] = "Character"
                    
            with open(schema_path, 'w') as f:
                json.dump(schema, f)
                
            return schema_path
        except Exception as e:
            print(f"⚠️ Schema Generation Failed: {e}")
            return None

    def save_vintage(self, r_path, func_name, label):
        """Saves a copy of the code to snapshots/func/timestamp_label.R"""
        target_dir = os.path.join(self.snapshot_dir, func_name)
        os.makedirs(target_dir, exist_ok=True)
        timestamp = int(time.time())
        filename = f"v{timestamp}_{label}.R"
        shutil.copy(r_path, os.path.join(target_dir, filename))

    def auto_format_file(self, r_path):
        """Runs 'styler' to mechanically fix whitespace."""
        cmd = ["Rscript", "-e", f"library(styler); style_file('{r_path}', strict=FALSE)"]
        subprocess.run(cmd, capture_output=True)

    def check_lint_score(self, r_path):
        """Checks style compliance (Lintr)."""
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
            f"cat(paste0('||COUNT||', length(issues)))"
        )
        cmd = ["Rscript", "-e", lint_cmd]
        res = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return int(res.stdout.split("||COUNT||")[1].strip())
        except:
            return 999

    def test_function_logic(self, r_path, func_name):
        """Runs the Unit Test wrapper. Returns (Pass/Fail, Message)."""
        wrapper_path = os.path.join(os.path.dirname(r_path), f"test_{func_name}.R")
        data_path = os.path.join(self.repo_root, "input_data.csv")
        
        r_script = f"""
        suppressPackageStartupMessages(library(dplyr))
        suppressPackageStartupMessages(library(lubridate))
        suppressPackageStartupMessages(library(readr))
        suppressPackageStartupMessages(library(stringr)) 
        
        tryCatch({{
            source("{r_path}")
            if(!file.exists("{data_path}")) stop("Data missing")
            df <- read.csv("{data_path}", colClasses = "character")
            
            # RUN IT
            res <- {func_name}(df)
            
            # Basic Validation
            if(nrow(res) == 0) stop("Empty Result")
            cat("PASS")
            
        }}, error = function(e) {{
            cat("FAIL:", e$message)
        }})
        """
        
        with open(wrapper_path, 'w') as f: f.write(r_script)
        
        try:
            res = subprocess.run(["Rscript", wrapper_path], capture_output=True, text=True)
            output = res.stdout.strip()
            if "PASS" in output: return True, "PASS"
            err_msg = output.replace("FAIL:", "").strip()
            if not err_msg: err_msg = res.stderr.strip()
            return False, err_msg
        finally:
            if os.path.exists(wrapper_path): os.remove(wrapper_path)

    def optimize_file(self, entry, force=False):
        r_path = entry['r_file']
        func_name = entry['r_function_name']
        print(f"\n🔍 Assessing {func_name}...")
        
        if not force:
            score = self.check_lint_score(r_path)
            if score == 0:
                print("   ✅ Code is clean. Skipping.")
                return

        self.save_vintage(r_path, func_name, "original")

        # 1. Prepare Refactoring Tools
        refactor_script = os.path.join(self.repo_root, "../migration/src/utils/refactor.R")
        # Fallback for relative paths
        if not os.path.exists(refactor_script):
             refactor_script = os.path.abspath("src/utils/refactor.R")
        
        # 2. Generate Schema for Type Awareness
        schema_path = self.generate_temp_schema()

        # 3. Setup the Agent Callback
        def check_callback(candidate_code):
            # A. Save Candidate
            with open(r_path, 'w') as f: f.write(candidate_code)
            
            # B. AST REFACTORING (Schema Aware)
            try:
                cmd = ["Rscript", refactor_script, r_path]
                if schema_path:
                    cmd.append(schema_path)
                    
                subprocess.run(cmd, check=True, capture_output=True)
            except Exception as e:
                # We do not crash the pipeline if refactoring fails, 
                # we let the Unit Tests catch logic errors.
                pass 

            # C. Mechanical Fixes (Styler)
            self.auto_format_file(r_path)
            
            # D. Logic Test
            is_valid, msg = self.test_function_logic(r_path, func_name)
            if not is_valid:
                return False, f"Runtime Error: {msg}"
                
            return True, "OK"

        # 4. Run Agent
        agent = RefiningAgent(OPTIMIZER_PROMPT, max_retries=3)
        
        with open(r_path, 'r') as f: original_code = f.read()
        
        print("   🤖 Agent activated. Generating & Testing...")
        final_code = agent.run(original_code, check_callback)
        
        # Cleanup temp schema
        if schema_path and os.path.exists(schema_path):
            os.remove(schema_path)
        
        if final_code:
            print("   ✅ Optimization SUCCESS.")
            self.save_vintage(r_path, func_name, "optimized_success")
        else:
            print("   ❌ Optimization FAILED. Reverting.")
            with open(r_path, 'w') as f: f.write(original_code)

    def run(self, force_all=False):
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        for entry in manifest:
            if entry.get('role') != 'controller':
                self.optimize_file(entry, force=force_all)

if __name__ == "__main__": 
    optimizer = CodeOptimizer()
    optimizer.run()