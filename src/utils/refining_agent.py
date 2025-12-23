import re
from src.utils.ollama_client import get_ollama_response

class RefiningAgent:
    def __init__(self, system_prompt, max_retries=3):
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.trace = []  # <--- NEW: Stores the conversation history

    def extract_code(self, response):
        """Extracts code from Markdown blocks or raw text."""
        if "```r" in response:
            return response.split("```r")[1].split("```")[0].strip()
        elif "```" in response:
            return response.split("```")[1].split("```")[0].strip()
        return response.strip()

    def run(self, original_code, check_callback):
        """
        Runs the refinement loop.
        check_callback(code) -> (bool_success, error_message)
        """
        self.trace = [] # Reset trace
        current_code = original_code
        error_history = ""

        # Step 0: Initial Attempt (Draft 1)
        # We treat the input code as 'Draft 1'. 
        # Usually, the Optimizer calls this with the Architect's draft.
        # Let's validate Draft 1 first.
        
        print("   [Agent] Validating initial draft...")
        success, error = check_callback(current_code)
        
        self.trace.append({
            "step": 0,
            "type": "Initial Validation",
            "code": current_code,
            "success": success,
            "error": error
        })

        if success:
            return current_code

        # Start the Retry Loop
        error_history = f"Attempt 1 Failed: {error}"
        
        for attempt in range(1, self.max_retries + 1):
            print(f"   [Agent] Asking LLM to fix (History: {attempt} failures)...")
            
            # Construct the Prompt
            prompt = (
                f"{self.system_prompt}\n\n"
                f"### CURRENT CODE:\n```r\n{current_code}\n```\n\n"
                f"### ERROR HISTORY:\n{error_history}\n\n"
                f"### TASK:\n"
                f"Fix the code to resolve the error. Return the FULL corrected R code."
            )

            # Call LLM
            response = get_ollama_response(prompt)
            new_code = self.extract_code(response)

            # Validate
            success, new_error = check_callback(new_code)

            # Record Trace
            self.trace.append({
                "step": attempt,
                "prompt": prompt,
                "response": response,
                "code_attempt": new_code,
                "success": success,
                "error": new_error
            })

            if success:
                return new_code
            
            # Update History
            error_history += f"\n\nAttempt {attempt+1} Failed: {new_error}"
            current_code = new_code # Iterate on the new draft

        print(f"   ❌ [Agent] Exhausted {self.max_retries} retries.")
        return None