import re
import textwrap  # <--- NEW IMPORT
from src.utils.ollama_client import get_ollama_response

class RefiningAgent:
    def __init__(self, system_prompt, max_retries=3):
        self.system_prompt = system_prompt
        self.max_retries = max_retries

    def extract_code(self, text):
        """Robustly extracts R code from Markdown blocks or raw text."""
        clean_text = ""
        
        # 1. Try Markdown blocks specifically for R
        if "```r" in text:
            clean_text = text.split("```r")[1].split("```")[0]
        elif "```R" in text:
            clean_text = text.split("```R")[1].split("```")[0]
        
        # 2. Try Generic blocks
        elif "```" in text:
            matches = re.findall(r"```(.*?)```", text, re.DOTALL)
            if matches:
                clean_text = max(matches, key=len)
        
        # 3. Heuristic/Fallback
        else:
            lines = text.split('\n')
            start_idx = 0
            for i, line in enumerate(lines):
                if "library(" in line or "function(" in line or "<-" in line:
                    start_idx = i
                    break
            clean_text = "\n".join(lines[start_idx:])

        # --- THE FIX: Clean up indentation and whitespace ---
        return textwrap.dedent(clean_text).strip()

    def run(self, initial_prompt, check_callback):
        full_prompt = f"{self.system_prompt}\n\nTASK:\n{initial_prompt}"
        response = get_ollama_response(full_prompt)
        candidate_code = self.extract_code(response)
        
        print(f"   [Agent] Draft 1 generated.")
        
        failure_history = []

        for attempt in range(1, self.max_retries + 1):
            success, error_msg = check_callback(candidate_code)
            
            if success:
                return candidate_code
            
            # Verbose Logging
            print(f"   [Agent] Attempt {attempt} failed.")
            print(f"   ⚠️ ERROR: {error_msg.replace(chr(10), ' ')[:300]}...") 
            
            failure_history.append(f"--- ATTEMPT {attempt} ---\nCODE:\n{candidate_code}\nERROR:\n{error_msg}\n")
            
            # DEFINE THE MISSING VARIABLE
            history_text = "\n".join(failure_history)
            
            print(f"   [Agent] Asking LLM to fix (History: {len(failure_history)} failures)...")
            
            fix_prompt = (
                f"{self.system_prompt}\n\n"
                f"The previous attempts FAILED. Use the error log to fix the code.\n"
                f"=== FAILURE HISTORY ===\n"
                f"{history_text}\n"
                f"=======================\n"
                f"TASK: Fix the code. Return ONLY the valid R syntax."
            )
            
            response = get_ollama_response(fix_prompt)
            candidate_code = self.extract_code(response)
            
        print(f"   ❌ [Agent] Exhausted {self.max_retries} retries.")
        return None