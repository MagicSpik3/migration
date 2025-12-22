import os
import json
import subprocess
import shutil
from src.utils.ollama_client import get_ollama_response

# The "Humanizer" Prompt
OPTIMIZER_PROMPT = """
You are a Senior R Developer. 
Refactor the following R code to be idiomatic, concise, and "human-like".

### GOALS:
1. **Readability:** Use `dplyr` pipes (`%>%`) and `lubridate`.
2. **Simplicity:** Replace complex logic with simple functions.
   - `ymd(paste(substr(...)))` --> `ymd(col)`
   - `date1 - date2` --> `as.numeric(date1 - date2)`
3. **Logic:** PRESERVE the existing business logic. Do not change variable names.

### INPUT CODE:
```r
{r_code}

OUTPUT:

Only the refactored R code. """

class CodeOptimizer: 
    def init(self, manifest_path="migration_manifest.json"): 
        self.manifest_path = os.path.abspath(manifest_path) 
        if not os.path.exists(self.manifest_path): 
            # Fallback 
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
        self.repo_root = os.path.dirname(os.path.dirname(self.manifest_path))

    def test_function(self, r_path, func_name):
        """
        Runs a micro-test to verify the function still works.
        Returns True if successful, False if broken.
        """
        # Create a temporary test harness wrapper
        wrapper_path = os.path.join(os.path.dirname(r_path), f"test_{func_name}.R")
        data_path = os.path.join(self.repo_root, "input_data.csv")
        

        # R Script to test the function
        r_script = f"""
        suppressPackageStartupMessages(library(dplyr))
        suppressPackageStartupMessages(library(lubridate))
        
        # Source the candidate function
        source("{r_path}")
        
        # Load real data
        if(!file.exists("{data_path}")) stop("No test data")
        df <- read.csv("{data_path}", colClasses = "character")
        
        # Try to run the function
        tryCatch({{
            res <- {func_name}(df)
            
            # VALIDATION CHECKS:
            if(nrow(res) == 0) stop("Optimizer produced empty dataframe!")
            
            # Check for specific logic (positive delay)
            if("delay_days" %in% names(res)) {{
                if(any(res$delay_days < 0)) stop("Optimizer broke the logic (Negative Delay)!")
            }}
            
            cat("PASS")
        }}, error = function(e) {{
            cat("FAIL: ", e$message)
        }})
        """
        
        with open(wrapper_path, 'w') as f:
            f.write(r_script)
            
        # Run Rscript
        try:
            result = subprocess.run(
                ["Rscript", wrapper_path], 
                capture_output=True, 
                text=True
            )
            output = result.stdout.strip()
            # print(f"    Test Output: {output}") # Debug
            
            return "PASS" in output
        finally:
            if os.path.exists(wrapper_path):
                os.remove(wrapper_path)


    def optimize_file(self, entry):
        r_path = entry['r_file']
        func_name = entry['r_function_name']
        
        print(f"🧬 Optimizing {func_name}...")
        
        # 1. Snapshot original (Safety)
        backup_path = r_path + ".bak"
        shutil.copy(r_path, backup_path)
        
        with open(r_path, 'r') as f:
            original_code = f.read()
            
        # 2. Ask LLM to Humanize
        prompt = OPTIMIZER_PROMPT.format(r_code=original_code)
        new_code = get_ollama_response(prompt)
        
        if "```r" in new_code: new_code = new_code.split("```r")[1].split("```")[0]
        elif "```" in new_code: new_code = new_code.split("```")[1].split("```")[0]
        
        # 3. Write Candidate Code
        with open(r_path, 'w') as f:
            f.write(new_code.strip())
            
        # 4. Verify Functionality
        is_valid = self.test_function(r_path, func_name)
        
        if is_valid:
            print(f"   ✅ Success! Code is cleaner and still works.")
            os.remove(backup_path) # Commit change
        else:
            print(f"   ❌ Regression! Optimizer broke the code. Reverting.")
            shutil.move(backup_path, r_path) # Revert     


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