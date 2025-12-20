import re

import subprocess
import re
import os
import tempfile

class PSPPValidator:
    @staticmethod
    def validate_execution(llm_code):
        """
        Wraps LLM code in a dummy SPSS definition and runs it via PSPP.
        Returns: (passed: bool, message: str)
        """
        # 1. Extract variable names the LLM is trying to label
        # Regex looks for: VALUE LABELS varname ...
        var_pattern = re.compile(r"VALUE LABELS\s+(\w+)", re.IGNORECASE)
        vars_found = var_pattern.findall(llm_code)
        
        if not vars_found:
            return False, "No VALUE LABELS commands found to test."

        # 2. Create the 'Wrapper' Syntax
        # We must define these variables before applying labels.
        # We make them numeric (F8.0) by default.
        setup_lines = ["DATA LIST LIST /"]
        for var in set(vars_found):
            setup_lines.append(f"    {var} (F8.0)")
        
        setup_lines.append(".") # End DATA LIST
        setup_lines.append("BEGIN DATA")
        setup_lines.append("1 " * len(set(vars_found))) # One row of dummy data
        setup_lines.append("END DATA.")
        setup_lines.append("") # Spacer
        
        # 3. Combine Setup + LLM Code
        full_syntax = "\n".join(setup_lines) + "\n" + llm_code

        # 4. Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sps', delete=False) as tmp:
            tmp.write(full_syntax)
            tmp_path = tmp.name

        # 5. Run PSPP
        # -o /dev/null discards the output table, we only care about stderr/exit code
        try:
            result = subprocess.run(
                ['pspp', '-o', '/dev/null', tmp_path],
                capture_output=True,
                text=True
            )
            
            # Cleanup
            os.remove(tmp_path)

            # 6. Check for Errors
            # PSPP usually exits with 0 even on syntax errors, so we must grep stderr/stdout
            # Look for lines starting with "error:" or "Error:"
            if result.returncode != 0 or "error:" in result.stderr.lower() or "error:" in result.stdout.lower():
                # Return the error log for debugging
                error_log = result.stderr + result.stdout
                return False, f"PSPP Syntax Error:\n{error_log}"

            return True, "PSPP executed successfully."

        except FileNotFoundError:
            return False, "PSPP executable not found. Is it in your PATH?"


class SPSSEvaluator:
    @staticmethod
    def check_value_label_syntax(text):
        """
        Checks for the specific error where LLM outputs "Label" = Value 
        instead of Value "Label".
        """
        # Old Pattern (Double quotes only): r'\d+\s+"[^"]+"'
        
        # New Pattern (Allows "Double" OR 'Single' quotes):
        good_pattern = re.compile(r"""\d+\s+["'][^"']+["']""")
        
        # Update bad pattern to match 'Label' = Value too
        bad_pattern = re.compile(r"""["'][^"']+["']\s*=\s*\d+""")

        failures = bad_pattern.findall(text)
        successes = good_pattern.findall(text)

        if failures:
            return False, f"Found {len(failures)} instances of inverted syntax (e.g., 'Label' = Value)."
        if not successes:
            return False, "No valid Value Label syntax found."
        return True, "Syntax looks correct."

    @staticmethod
    def check_hallucinations(text):
        """Checks for known hallucinated commands from Qwen/Llama."""
        forbidden_terms = [
            "!GETDEFS", 
            "!ERROR", 
            "VALID(", 
            "!IF (NOT",
            "```spss",  # Markdown blocks should ideally be stripped, but checking anyway
            "```"
        ]
        found = [term for term in forbidden_terms if term in text]
        if found:
            return False, f"Found forbidden terms/hallucinations: {found}"
        return True, "No hallucinations detected."

    @staticmethod
    def check_terminators(text):
        """SPSS commands must end with a period."""
        # Strip whitespace and check last char
        clean = text.strip()
        if not clean.endswith('.'):
            return False, "Code block does not end with a period terminator (.)"
        return True, "Terminators look okay."

    @staticmethod
    def check_variable_coverage(text, expected_vars):
        """Ensures all R variables got an SPSS command."""
        missing = []
        for var in expected_vars:
            # Look for 'VALUE LABELS varname' or 'VARIABLE LABELS varname'
            if f"{var}" not in text:
                missing.append(var)
        
        if missing:
            return False, f"Missing definitions for variables: {missing}"
        return True, "All variables covered."