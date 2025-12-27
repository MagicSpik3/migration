import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import ARCHITECT_PROMPT

class TestArchitectBoundaries(unittest.TestCase):

    def generate_code(self, spec, schema="`id`, `val`"):
        """Helper to get R code from the Architect."""
        full_prompt = ARCHITECT_PROMPT.format(
            target_name="boundary_test_func",
            spec_content=spec,
            columns=schema,
            glossary="No specific glossary terms."
        )
        
        print(f"\n   [Thinking] Testing Boundary Spec: '{spec[:40]}...'")
        raw_response = get_ollama_response(full_prompt)
        
        if "```r" in raw_response: 
            return raw_response.split("```r")[1].split("```")[0].strip()
        elif "```" in raw_response: 
            return raw_response.split("```")[1].split("```")[0].strip()
        return raw_response.strip()

    def test_age_groups_gap_risk(self):
        """
        Scenario: 'Child is under 18, Adult is 18 to 65, Senior is over 65.'
        Risk: If code is `age < 18`, `age >= 18 & age < 65`, `age > 65`... then exactly 65 is NULL.
        Expectation: Code must cover 65 explicitly (e.g., `<= 65` or `>= 65`) or use a catch-all.
        """
        spec = "Categorize age: 'Child' (< 18), 'Adult' (18 to 65), 'Senior' (> 65)."
        schema = "`id`, `age`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output Snippet]:\n{code}")
        
        # 1. Must use case_when (from Rule 6)
        self.assertIn("case_when", code)
        
        # 2. Check for Boundary Safety at 65
        # It must be EITHER included in Adult (<= 65) OR included in Senior (>= 65)
        # OR handled by a default TRUE
        has_inclusive_upper = "<= 65" in code or "between(age, 18, 65)" in code
        has_inclusive_lower = ">= 65" in code
        has_catch_all = "TRUE ~" in code
        
        self.assertTrue(has_inclusive_upper or has_inclusive_lower or has_catch_all,
                        "❌ Boundary Error: Age 65 might be dropped! Found no inclusive operator or catch-all.")

    def test_income_brackets_overlap_risk(self):
        """
        Scenario: 'Low < 30k, Middle 30k-100k, High > 100k'.
        Risk: Does 30k go to Low or Middle? Code must decide.
        Expectation: Operators must be distinct (e.g. `< 30000` and `>= 30000`).
        """
        spec = "Classify income: Low (< 30,000), Middle (30,000 - 100,000), High (> 100,000)."
        schema = "`id`, `income`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output Snippet]:\n{code}")
        
        # Check specific handling of the 30,000 boundary
        # We look for the number without commas (Architect should clean it)
        self.assertIn("30000", code)
        
        # Ensure we don't have a gap at 100,000
        # If High is > 100000, Middle MUST be <= 100000 or catch-all.
        has_inclusive_mid = "<= 100000" in code or "between(income, 30000, 100000)" in code
        has_inclusive_high = ">= 100000" in code
        has_catch_all = "TRUE ~" in code
        
        self.assertTrue(has_inclusive_mid or has_inclusive_high or has_catch_all,
                        "❌ Boundary Error: Income 100,000 might be dropped!")

    def test_categorical_catch_all(self):
        """
        Scenario: Map specific codes to labels.
        Risk: Unexpected codes (garbage data) become NA.
        Expectation: A 'TRUE ~ "Unknown"' or similar catch-all.
        """
        spec = "Map status codes: 1=Active, 2=Paused, 3=Cancelled. Handle errors as 'Unknown'."
        schema = "`id`, `status`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output Snippet]:\n{code}")
        
        self.assertIn("Active", code)
        self.assertIn("Paused", code)
        
        # Must have a fallback
        self.assertIn("TRUE", code, "❌ Missing catch-all (TRUE ~ ...) for unknown status codes.")
        self.assertIn("Unknown", code)

if __name__ == "__main__":
    unittest.main()