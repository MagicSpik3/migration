import os
import json
import subprocess
import shutil
import time
from src.utils.refining_agent import RefiningAgent
from src.specs.prompts import OPTIMIZER_PROMPT_V2

class CodeOptimizer: 
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
            
        print(f"   ℹ️  Optimizer using manifest at: {self.manifest_path}")

        self.snapshot_dir = os.path.join(self.project_root, "snapshots")
        self.debug_dir = os.path.join(self.project_root, "debug_traces")
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.debug_dir, exist_ok=True)
        
        self.refactor_script = os.path.join(os.path.dirname(__file__), "../utils/refactor.R")
        if not os.path.exists(self.refactor_script):
             self.refactor_script = os.path.abspath("src/utils/refactor.R")

        self.raw_data_path = os.path.join(self.project_root, "input_data.csv")
        self.current_data_path = os.path.join(self.project_root, "temp_pipeline_state.csv")
        
        if os.path.exists(self.raw_data_path):
            shutil.copy(self.raw_data_path, self.current_data_path)

    def save_vintage(self, r_path, func_name, label):
        target_dir = os.path.join(self.snapshot_dir, func_name)
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(r_path, os.path.join(target_dir, f"v{int(time.time())}_{label}.R"))

    def dump_debug_trace(self, func_name, trace):
        report_path = os.path.join(self.debug_dir, f"FAILED_{func_name}.txt")
        with open(report_path, 'w') as f:
            f.write(f"=== DEBUG TRACE FOR {func_name} ===\n\n")
            for entry in trace:
                f.write(f"--- STEP {entry['step']} ---\n")
                if 'code_attempt' in entry: f.write(f"[CODE ATTEMPTED]:\n{entry['code_attempt']}\n\n")
                if 'prompt' in entry: f.write(f"[PROMPT SENT]:\n{entry['prompt']}\n\n")
                if 'response' in entry: f.write(f"[LLM REPLY]:\n{entry['response']}\n\n")
                f.write(f"[RESULT]: Success={entry['success']}\n[ERROR]: {entry.get('error', 'None')}\n{'='*40}\n\n")
        print(f"   🐛 Debug trace saved to: {report_path}")

    def check_lint_status(self, r_path):
        lint_cmd = (
            f"library(lintr); "
            f"custom_linters <- linters_with_defaults(line_length_linter = line_length_linter(120)); "
            f"issues <- lint('{r_path}', linters = custom_linters); "
            f"if(length(issues) > 0) {{ cat(paste(sapply(issues, function(x) paste0('Line ', x$line_number, ': ', x$message)), collapse='||')) }} else {{ cat('') }}"
        )
        try:
            res = subprocess.run(["Rscript", "-e", lint_cmd], capture_output=True, text=True)
            output = res.stdout.strip()
            if not output: return 0, "No issues."
            issues = output.split("||")
            return len(issues), "\n".join(issues)
        except Exception as e:
            return 1, f"Linting failed: {e}"

    def test_function_logic(self, r_path, func_name):
        data_path = self.current_data_path
        wrapper_path = os.path.join(os.path.dirname(r_path), f"test_{func_name}_opt.R")
        
        # ADDED stringr here
        r_script = f"""
        suppressPackageStartupMessages(library(dplyr))
        suppressPackageStartupMessages(library(lubridate))
        suppressPackageStartupMessages(library(readr))
        suppressPackageStartupMessages(library(stringr)) 
        
        tryCatch({{
            source("{r_path}")
            if(!file.exists("{data_path}")) stop("Data missing at {data_path}")
            
            df <- read.csv("{data_path}", colClasses = "character", check.names = FALSE)
            res <- {func_name}(df)
            
            if(!is.data.frame(res)) stop("Result is not a dataframe")
            if(nrow(res) == 0) stop("Empty Result returned")
            
            cat("PASS")
        }}, error = function(e) {{
            cat("FAIL: ", conditionMessage(e))
        }})
        """       
        
        try:
            with open(wrapper_path, 'w') as f: f.write(r_script)
            res = subprocess.run(["Rscript", wrapper_path], capture_output=True, text=True)
            output = res.stdout.strip()
            
            if "PASS" in output: return True, "PASS"
            err_msg = output.replace("FAIL:", "").strip()
            if not err_msg: err_msg = res.stderr.strip()
            return False, err_msg
        except Exception as e:
            return False, str(e)
        finally:
            if os.path.exists(wrapper_path): os.remove(wrapper_path)

    def update_pipeline_state(self, r_path, func_name):
        data_path = self.current_data_path
        wrapper_path = os.path.join(os.path.dirname(r_path), f"update_{func_name}_state.R")
        
        # ADDED stringr here as well
        r_script = f"""
        suppressPackageStartupMessages(library(dplyr))
        suppressPackageStartupMessages(library(lubridate))
        suppressPackageStartupMessages(library(readr))
        suppressPackageStartupMessages(library(stringr))
        
        tryCatch({{
            source("{r_path}")
            df <- read.csv("{data_path}", colClasses = "character", check.names = FALSE)
            res <- {func_name}(df)
            
            if("id" %in% names(res)) {{
                write.csv(res, "{data_path}", row.names = FALSE)
                cat("UPDATED")
            }} else {{
                cat("SKIPPED (No 'id' column - Assumed Summary Report)")
            }}

        }}, error = function(e) {{
            cat(paste("FAIL:", conditionMessage(e)))
        }})
        """
        try:
            with open(wrapper_path, 'w') as f: f.write(r_script)
            res = subprocess.run(["Rscript", wrapper_path], capture_output=True, text=True)
            output = res.stdout.strip()
            
            if "UPDATED" in output:
                print(f"      💾 Pipeline State Updated ({func_name} preserved 'id')")
            elif "SKIPPED" in output:
                print(f"      ⏩ Pipeline State Preserved ({func_name} dropped 'id')")
            elif "FAIL" in output:
                print(f"      ⚠️  State Update FAILED: {output}")
        finally:
            if os.path.exists(wrapper_path): os.remove(wrapper_path)

    def optimize_file(self, entry, force=False):
        r_path = entry['r_file']
        func_name = entry['r_function_name']
        
        if not os.path.exists(r_path):
            print(f"   ⚠️ Skipping {func_name} (File not found)")
            return

        print(f"\n🔍 Assessing {func_name}...")
        self.save_vintage(r_path, func_name, "original")
        
        draft_passed, draft_msg = self.test_function_logic(r_path, func_name)
        working_draft_code = None
        
        if draft_passed:
            with open(r_path, 'r') as f: working_draft_code = f.read()
            lint_score, lint_msg = self.check_lint_status(r_path)
            if lint_score == 0 and not force:
                print("   ✅ Draft passed logic and style. No optimization needed.")
                self.update_pipeline_state(r_path, func_name)
                return
            print(f"   ⚠️ Logic PASS, but found {lint_score} style issues. Optimizing...")
            logic_status = "PASS"
        else:
            print(f"   ⚠️ Logic FAIL ({draft_msg}). Optimizing to FIX...")
            logic_status = f"FAIL: {draft_msg}"

        def check_callback(candidate_code):
            with open(r_path, 'w') as f: f.write(candidate_code)
            subprocess.run(["Rscript", self.refactor_script, r_path], capture_output=True)
            is_valid, msg = self.test_function_logic(r_path, func_name)
            if not is_valid: return False, f"Runtime Error: {msg}"
            return True, "OK"

        with open(r_path, 'r') as f: current_code = f.read()
        prompt = OPTIMIZER_PROMPT_V2.format(
            logic_status=logic_status,
            lint_issues="Optimize Style and Logic",
            r_code="{r_code}" 
        )
        
        agent = RefiningAgent(prompt, max_retries=3)
        print("   🤖 Agent activated...")
        final_code = agent.run(current_code, check_callback)

        if final_code:
            print("   ✅ Optimization SUCCESS.")
            self.save_vintage(r_path, func_name, "optimized")
            self.update_pipeline_state(r_path, func_name)
        else:
            print("   ❌ Optimization FAILED (Could not pass validation).")
            self.dump_debug_trace(func_name, agent.trace)
            if working_draft_code:
                print("   ↩️  Reverting to Working Draft (Safety Latch).")
                with open(r_path, 'w') as f: f.write(working_draft_code)
                if self.test_function_logic(r_path, func_name)[0]:
                    self.update_pipeline_state(r_path, func_name)
            else:
                print("   ⚠️ No working draft to revert to.")

    def run(self, force_all=False):
        print(f"   Loading Manifest for Optimization from {self.manifest_path}...")
        if not os.path.exists(self.manifest_path):
             print("   ❌ Manifest file missing.")
             return

        if os.path.exists(self.raw_data_path):
            shutil.copy(self.raw_data_path, self.current_data_path)
            print("   🔄 Pipeline Data Reset to Raw Input.")

        with open(self.manifest_path, 'r') as f: manifest = json.load(f)
        
        for entry in manifest:
            if entry.get('role') == 'logic':
                self.optimize_file(entry, force=force_all)
        
        if os.path.exists(self.current_data_path):
            os.remove(self.current_data_path)

if __name__ == "__main__": 
    optimizer = CodeOptimizer()
    optimizer.run()