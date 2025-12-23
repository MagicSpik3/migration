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
Refactor this code to be idiomatic `tidyverse` and FIX errors.

### CONTEXT:
- **Logic Status:** {logic_status}
- **Style Issues:** {lint_issues}

### RULES:
1. **Type Safety (CRITICAL):**
   - The input `df` is ALL CHARACTERS.
   - **CAST EVERYTHING:** `cut(as.numeric(age), ...)`
   - **CAST EVERYTHING:** `between(as.numeric(age), 18, 64)`

2. **Date Math (STRICT):**
   - ❌ WRONG: `as.numeric(d1 - d2, units="days")`
   - ✅ RIGHT: `as.numeric(difftime(d1, d2, units="days"))`
   - **Inherited Columns:** If `date_death` exists from step 1, DO NOT re-parse it with `ymd()`.

3. **Lubridate Syntax (CRITICAL):**
   - ❌ WRONG: `ymd(year_str, month_str, day_str)` <- ymd() takes ONE argument!
   - ✅ RIGHT: `ymd(date_string)`
   - **Extraction:** Before using `month()` or `year()`, YOU MUST CAST: `month(ymd(date_col))`.

4. **Math Safety (CRITICAL):**
   - ❌ WRONG: `mean(delay_days)` (Fails on character input)
   - ✅ RIGHT: `mean(as.numeric(delay_days), na.rm = TRUE)`
   - ALWAYS use `as.numeric()` inside aggregation functions like `mean`, `sum`, `max`.

5. **Pipeline Continuity:**
   - If summarizing: `write.csv(summary_df, ...); return(df)`
   - Do NOT shadow function names (use `summary_df`, not `func_name`).

6. **Output Hygiene:**
   - RETURN ONLY THE CODE.
   - Do NOT include "Explanation:" or text outside the code block.

### INPUT:
```r
{r_code}
"""

class CodeOptimizer: 
    def __init__(self, manifest_path="migration_manifest.json"): 
        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
            
        with open(self.manifest_path, 'r') as f:
            data = json.load(f)
            first_r_file = data[0]['r_file']
            if not os.path.isabs(first_r_file):
                first_r_file = os.path.abspath(os.path.join(os.path.dirname(self.manifest_path), first_r_file))
            self.repo_root = os.path.dirname(os.path.dirname(first_r_file))
        
        self.snapshot_dir = os.path.join(self.repo_root, "snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def generate_temp_schema(self):
        csv_path = os.path.join(self.repo_root, "input_data.csv")
        schema_path = os.path.join(self.repo_root, "temp_schema_types.json")
        if not os.path.exists(csv_path): return None
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
            schema = {}
            for col in headers:
                if any(x in col.lower() for x in ["date", "dob", "dod", "dor"]):
                    schema[col] = "Date"
                else:
                    schema[col] = "Character"
            with open(schema_path, 'w') as f: json.dump(schema, f)
            return schema_path
        except: return None

    def save_vintage(self, r_path, func_name, label):
        target_dir = os.path.join(self.snapshot_dir, func_name)
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(r_path, os.path.join(target_dir, f"v{int(time.time())}_{label}.R"))

    def auto_format_file(self, r_path):
        subprocess.run(["Rscript", "-e", f"library(styler); style_file('{r_path}', strict=FALSE)"], capture_output=True)

    def check_lint_status(self, r_path):
        """Returns (score, details_string)"""
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
            # Output format: LINE::MESSAGE
            f"cat(paste(sapply(issues, function(x) paste0('Line ', x$line_number, ': ', x$message)), collapse='||'))"
        )
        res = subprocess.run(["Rscript", "-e", lint_cmd], capture_output=True, text=True)
        
        output = res.stdout.strip()
        if not output: return 0, "No issues."
        
        # Clean up R output garbage if present
        if "||" in output:
            issues = output.split("||")
            # Filter out empty strings
            issues = [i.strip() for i in issues if i.strip()]
            return len(issues), "\n".join(issues)
        
        # Fallback if no delimiter found but text exists
        return 1, output


    def test_function_logic(self, r_path, func_name):
        wrapper_path = os.path.join(os.path.dirname(r_path), f"test_{func_name}.R")
        data_path = os.path.join(self.repo_root, "input_data.csv")
        
        r_script = f"""
        suppressPackageStartupMessages(library(dplyr))
        suppressPackageStartupMessages(library(lubridate))
        suppressPackageStartupMessages(library(readr))
        suppressPackageStartupMessages(library(stringr)) 
        
        # Helper to print errors safely
        print_error <- function(e) {{
            cat("FAIL:", conditionMessage(e))
            # Try to dig into rlang/dplyr chained errors
            if (!is.null(e$parent)) {{
                cat("\\nCaused by: ", conditionMessage(e$parent))
            }}
            # Dump warnings too just in case
            if (exists("last_dplyr_warnings")) {{
                cat("\\nWarnings:\\n")
                print(dplyr::last_dplyr_warnings())
            }}
        }}

        tryCatch({{
            source("{r_path}")
            if(!file.exists("{data_path}")) stop("Data missing at {data_path}")
            
            # Read STRICTLY as character to test robustness
            df <- read.csv("{data_path}", colClasses = "character", check.names = FALSE)
            
            # Print schema for debugging
            # cat("DEBUG SCHEMA:", paste(names(df), collapse=", "), "\\n")
            
            res <- {func_name}(df)
            
            if(nrow(res) == 0) stop("Empty Result")
            cat("PASS")
            
        }}, error = print_error)
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

    def dump_debug_trace(self, func_name, trace):
        debug_dir = os.path.join(self.repo_root, "debug_traces")
        os.makedirs(debug_dir, exist_ok=True)
        report_path = os.path.join(debug_dir, f"FAILED_{func_name}.txt")
        with open(report_path, 'w') as f:
            f.write(f"=== DEBUG TRACE FOR {func_name} ===\n\n")
            for entry in trace:
                f.write(f"--- STEP {entry['step']} ---\n")
                if 'code_attempt' in entry: f.write(f"[CODE ATTEMPTED]:\n{entry['code_attempt']}\n\n")
                elif 'code' in entry: f.write(f"[CODE ATTEMPTED]:\n{entry['code']}\n\n")
                if 'prompt' in entry: f.write(f"[PROMPT SENT]:\n{entry['prompt']}\n\n") # NO TRUNCATION
                if 'response' in entry: f.write(f"[LLM REPLY]:\n{entry['response']}\n\n")
                f.write(f"[RESULT]: Success={entry['success']}\n[ERROR]: {entry['error']}\n{'='*40}\n\n")
        print(f"   🐛 Debug trace saved to: {report_path}")

    def optimize_file(self, entry, force=False):
        r_path = entry['r_file']
        func_name = entry['r_function_name']
        print(f"\n🔍 Assessing {func_name}...")
        
        self.save_vintage(r_path, func_name, "original")
        
        # 1. Baseline Check: Does it work ALREADY?
        # We mechanically fix format first to give it a fair chance
        self.auto_format_file(r_path)
        is_valid, initial_msg = self.test_function_logic(r_path, func_name)
        lint_score, lint_details = self.check_lint_status(r_path)
        
        if is_valid and lint_score == 0 and not force:
            print("   ✅ Code passed logic and linting. No optimization needed.")
            return

        # Prepare Context for Agent
        if is_valid:
            print(f"   ⚠️ Logic PASS, but found {lint_score} style issues. Optimizing for Style...")
            logic_status = "PASSING. PRESERVE BEHAVIOR. FOCUS ON STYLE."
        else:
            print(f"   ⚠️ Logic FAIL ({initial_msg}). Optimizing for Logic...")
            logic_status = f"FAILING. Runtime Error: {initial_msg}"

        # Refactor Setup
        refactor_script = os.path.join(self.repo_root, "../migration/src/utils/refactor.R")
        if not os.path.exists(refactor_script): refactor_script = os.path.abspath("src/utils/refactor.R")
        schema_path = self.generate_temp_schema()

        def check_callback(candidate_code):
            with open(r_path, 'w') as f: f.write(candidate_code)
            try:
                cmd = ["Rscript", refactor_script, r_path]
                if schema_path: cmd.append(schema_path)
                subprocess.run(cmd, check=True, capture_output=True)
            except: pass
            self.auto_format_file(r_path)
            is_valid, msg = self.test_function_logic(r_path, func_name)
            if not is_valid: return False, f"Runtime Error: {msg}"
            return True, "OK"

        # Update Prompt with specifics
        specific_prompt = OPTIMIZER_PROMPT.format(
            logic_status=logic_status,
            lint_issues=lint_details,
            r_code="{r_code}" # Leave placeholder for Agent
        )
        
        agent = RefiningAgent(specific_prompt, max_retries=3)
        with open(r_path, 'r') as f: original_code = f.read()
        
        print("   🤖 Agent activated...")
        final_code = agent.run(original_code, check_callback)
        if schema_path and os.path.exists(schema_path): os.remove(schema_path)
        
        if final_code:
            print("   ✅ Optimization SUCCESS.")
            self.save_vintage(r_path, func_name, "optimized_success")
        else:
            print("   ❌ Optimization FAILED. Reverting.")
            self.dump_debug_trace(func_name, agent.trace)
            with open(r_path, 'w') as f: f.write(original_code)

    def run(self, force_all=False):
        with open(self.manifest_path, 'r') as f: manifest = json.load(f)
        for entry in manifest:
            if entry.get('role') != 'controller': self.optimize_file(entry, force=force_all)

if __name__ == "__main__": 
    optimizer = CodeOptimizer()
    optimizer.run()