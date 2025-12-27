import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import ARCHITECT_PROMPT

class TestArchitectAdvanced(unittest.TestCase):

    def generate_code(self, spec, schema="`id`, `val1`, `val2`"):
        """Helper: Generates R code from a spec using the Architect Prompt."""
        full_prompt = ARCHITECT_PROMPT.format(
            target_name="advanced_test_func",
            spec_content=spec,
            columns=schema,
            glossary="No specific glossary terms."
        )
        
        # --- DEBUG LOGGING ---
        print(f"\n[DEBUG PROMPT sent to LLM]:\n{'-'*40}\n{full_prompt}\n{'-'*40}")
        
        print(f"   [Thinking] Asking LLM to Architect '{spec[:30]}...'")
        raw_response = get_ollama_response(full_prompt)
        
        print(f"\n[DEBUG RESPONSE from LLM]:\n{'-'*40}\n{raw_response}\n{'-'*40}")
        # ---------------------
        
        if "```r" in raw_response: 
            return raw_response.split("```r")[1].split("```")[0].strip()
        elif "```" in raw_response: 
            return raw_response.split("```")[1].split("```")[0].strip()
        return raw_response.strip()

    def test_pivot_longer(self):
        """
        Scenario: Convert 'Wide' data to 'Long' format.
        Challenge: LLMs often use the outdated `gather()` function.
        Expectation: Must use modern `tidyr::pivot_longer()`.
        """
        print("\n🧪 Scenario: Reshaping (Pivot Longer)...")
        spec = "Convert the columns 'q1_score', 'q2_score', 'q3_score' into rows defined by 'question' and 'score'."
        schema = "`id`, `q1_score`, `q2_score`, `q3_score`, `region`"
        
        code = self.generate_code(spec, schema)
        
        # 1. Must use pivot_longer
        self.assertIn("pivot_longer", code, "❌ Architect used outdated syntax (like gather). Wanted 'pivot_longer'.")
        # 2. Must verify columns
        self.assertIn("q1_score", code)
        self.assertIn("q3_score", code)

    def test_left_join_logic(self):
        """
        Scenario: Merging two datasets.
        """
        print("\n🧪 Scenario: Joins (Left Join)...")
        spec = "Enrich the main data by joining with the 'demographics' lookup table on 'patient_id'."
        schema = "`patient_id`, `diagnosis_code`"
        
        code = self.generate_code(spec, schema)
        
        self.assertIn("left_join", code)
        self.assertIn("demographics", code)

    def test_string_cleaning(self):
        """
        Scenario: Regex string manipulation.
        """
        print("\n🧪 Scenario: String Cleaning (Regex)...")
        spec = "Clean the 'id' column by removing the prefix 'ID-'."
        schema = "`id`, `name`"
        
        code = self.generate_code(spec, schema)
        
        self.assertTrue("str_remove" in code or "str_replace" in code, 
                        "❌ Architect failed to use stringr functions for cleaning.")
        self.assertIn("ID-", code)

    def test_complex_case_when(self):
        """
        Scenario: Multi-condition logic.
        Challenge: Correct syntax for `case_when`.
        """
        print("\n🧪 Scenario: Complex Conditional (case_when)...")
        spec = "Categorize 'risk' as 'High' if age > 60 OR bmi > 30, otherwise 'Low'."
        schema = "`id`, `age`, `bmi`"
        
        code = self.generate_code(spec, schema)
        
        self.assertIn("case_when", code)
        self.assertIn("High", code)
        self.assertIn("Low", code)
        
        # ROBUST ASSERTION:
        # Check for explicit OR ("|") OR sequential logic (multiple "High" branches)
        has_explicit_or = "|" in code
        has_sequential_logic = code.count('"High"') >= 2 or code.count("'High'") >= 2
        
        self.assertTrue(has_explicit_or or has_sequential_logic, 
                        f"❌ Logic misses OR condition. Expected '|' operator or sequential branches.\nCode:\n{code}")

if __name__ == "__main__":
    unittest.main()