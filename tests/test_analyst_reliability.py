import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response
# FIX: Import the REAL prompt, don't use a local weak one
from src.specs.prompts import ANALYST_PROMPT

class TestAnalystReliability(unittest.TestCase):

    def analyze(self, spss_code):
        """Helper to get the Analyst's Spec using the production prompt."""
        # Use the real prompt template
        prompt = ANALYST_PROMPT.format(
            filename="test_snippet",
            spss_code=spss_code
        )
        return get_ollama_response(prompt).strip().lower()

    def test_conflict_code_vs_comment(self):
        """
        Scenario: The comment lies.
        SPSS: * Filter for Adults.
        Code: SELECT IF age < 18.
        Expectation: Spec MUST say "keep if age < 18" (Children).
        """
        print("\n🧪 Test: Analyst Truthfulness (The Lying Comment)...")
        spss = """
        * FILTER FOR ADULTS.
        SELECT IF (age < 18).
        """
        
        spec = self.analyze(spss)
        print(f"   [Spec snippet]: {spec[:100]}...")
        
        # It must describe the CODE
        self.assertIn("18", spec)
        self.assertTrue("<" in spec or "less" in spec or "under" in spec, 
                        "❌ Analyst was fooled by the comment! Code actually filters for children (< 18).")
        
        # It must NOT blindly repeat the lie
        if "adult" in spec:
            self.assertFalse("filter for adults" in spec, 
                             "❌ Analyst blindly repeated 'Filter for Adults' despite the code saying < 18.")

    def test_syntax_resilience_abbreviations(self):
        """
        Scenario: SPSS allows abbreviations (COMP, FREQ).
        """
        print("\n🧪 Test: Syntax Resilience (Abbreviations)...")
        spss = """
        COMP new_val = old_val * 100.
        FREQ VARS=new_val.
        """
        
        spec = self.analyze(spss)
        
        self.assertTrue("calc" in spec or "compute" in spec or "multiply" in spec, 
                        "❌ Analyst failed to parse 'COMP'.")
        self.assertTrue("count" in spec or "frequenc" in spec, 
                        "❌ Analyst failed to parse 'FREQ'.")

    def test_noise_filtering(self):
        """
        Scenario: Code is full of junk (TITLE, CACHE).
        Expectation: Spec focuses ONLY on logic.
        """
        print("\n🧪 Test: Noise Filtering (Ignoring Non-Logic)...")
        spss = """
        TITLE "Annual Report 2024".
        CACHE.
        EXECUTE.
        COMPUTE flag = 1.
        PRINT / "Processing Complete".
        """
        
        spec = self.analyze(spss)
        print(f"   [Spec snippet]: {spec[:100]}...")
        
        # Should mention 'flag'
        self.assertIn("flag", spec)
        
        # Should NOT mention technical noise
        self.assertNotIn("cache", spec, "❌ Analyst included technical noise (CACHE).")
        self.assertNotIn("execute", spec, "❌ Analyst included technical noise (EXECUTE).")
        self.assertNotIn("title", spec, "❌ Analyst included technical noise (TITLE).")

if __name__ == "__main__":
    unittest.main()