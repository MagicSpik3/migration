import re
import subprocess
import os
from src.utils.ollama_client import get_ollama_response

class SPSSRefiningAgent:
    def __init__(self, system_prompt, max_retries=3):
        self.system_prompt = system_prompt
        self.max_retries = max_retries

    def extract_code(self, text):
        """
        Robustly extracts code from Markdown blocks or raw text.
        """
        # Look for ```spss ... ``` or ``` ... ```
        pattern = r"```(?:spss)?(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return max(matches, key=len).strip()
        
        # Heuristic for raw text
        commands = ["GET DATA", "DATA LIST", "COMPUTE", "VARIABLE LABELS", "VALUE LABELS", "SELECT IF", "AGGREGATE", "EXECUTE", "FORMATS"]
        lines = text.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if any(cmd in line.upper() for cmd in commands):
                start_idx = i
                break
        
        return "\n".join(lines[start_idx:]).strip()

    def generate_and_refine(self, prompt, check_callback):
        """
        Generates code, runs the check_callback (compilation), 
        and iteratively fixes errors using a history of failures.
        """
        # 1. Initial Draft
        full_prompt = f"{self.system_prompt}\n\nTASK:\n{prompt}"
        response = get_ollama_response(full_prompt)
        candidate_code = self.extract_code(response)
        
        print(f"   [Agent] Draft 1 generated.")
        
        # STORE HISTORY: List of tuples (attempt_number, code, error)
        failure_history = []

        for attempt in range(1, self.max_retries + 1):
            # 2. Check (Compile)
            success, error_msg = check_callback(candidate_code)
            
            if success:
                print(f"   [Agent] Success on attempt {attempt}!")
                return candidate_code
            
            # Log failure
            print(f"   [Agent] Attempt {attempt} failed.")
            print(f"   [DEBUG] Compiler Error:\n{'-'*20}\n{error_msg}\n{'-'*20}")
            
            # Add to history
            failure_history.append(f"--- ATTEMPT {attempt} ---\nCODE:\n{candidate_code}\nERROR:\n{error_msg}\n")
            
            # 3. Refine (Feed COMPLETE history back to LLM)
            print(f"   [Agent] Asking LLM to fix (History: {len(failure_history)} failures)...")
            
            history_text = "\n".join(failure_history)
            
            fix_prompt = (
                f"{self.system_prompt}\n\n"
                f"The following SPSS code attempts have FAILED. Do NOT repeat these mistakes.\n\n"
                f"=== FAILURE HISTORY ===\n"
                f"{history_text}\n"
                f"=======================\n\n"
                f"TASK: Analyze the history above. Fix the code to resolve the errors. "
                f"Return ONLY the valid SPSS syntax."
            )
            
            response = get_ollama_response(fix_prompt)
            candidate_code = self.extract_code(response)
            
        raise RuntimeError(f"Failed to generate valid SPSS after {self.max_retries} attempts.")