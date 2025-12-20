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
            # Return the largest block (heuristic: usually the main code)
            return max(matches, key=len).strip()
        
        # If no markdown, assume the whole text is code, 
        # but strip conversational prefixes if they exist.
        # Simple heuristic: find the first known SPSS command
        commands = ["GET DATA", "DATA LIST", "COMPUTE", "VARIABLE LABELS", "VALUE LABELS", "SELECT IF", "AGGREGATE"]
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
        and iteratively fixes errors.
        
        check_callback: function(spss_code) -> (success: bool, error_msg: str)
        """
        # 1. Initial Draft
        full_prompt = f"{self.system_prompt}\n\nTASK:\n{prompt}"
        response = get_ollama_response(full_prompt)
        candidate_code = self.extract_code(response)
        
        print(f"   [Agent] Draft 1 generated.")

        for attempt in range(1, self.max_retries + 1):
            # 2. Check (Compile)
            success, error_msg = check_callback(candidate_code)
            
            if success:
                print(f"   [Agent] Success on attempt {attempt}!")
                return candidate_code
            
            print(f"   [Agent] Attempt {attempt} failed. Retrying...")
            
            # 3. Refine (Feed error back to LLM)
            fix_prompt = (
                f"{self.system_prompt}\n\n"
                f"The following SPSS code produced a syntax error:\n"
                f"```spss\n{candidate_code}\n```\n\n"
                f"ERROR MESSAGE:\n{error_msg}\n\n"
                f"TASK: Fix the code to resolve the error. Return ONLY the fixed SPSS syntax."
            )
            
            response = get_ollama_response(fix_prompt)
            candidate_code = self.extract_code(response)
            
        raise RuntimeError(f"Failed to generate valid SPSS after {self.max_retries} attempts.")