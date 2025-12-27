import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response

# We need the Analyst Prompt. 
# Since it might be buried in src/specs/analyst.py, let's define a helper to simulate it
# or import it if you extracted it to prompts.py (which we should do eventually).
# For now, we'll simulate the Analyst's core task.

ANALYST_PROMPT_TEMPLATE = """
You are a Systems Analyst. 
Analyze this SPSS syntax and write a clear, step-by-step requirement specification in Markdown.

### SPSS CODE:
{spss_code}

### OUTPUT:
Markdown specification.
"""

class TestAnalystScenarios(unittest.TestCase):

    def analyze_spss(self, spss_snippet):
        """Helper: Simulates the Analyst converting SPSS to a Spec."""
        prompt = ANALYST_PROMPT_TEMPLATE.format(spss_code=spss_snippet)
        
        # Use our deterministic client (Temperature 0.0)
        return get_ollama_response(prompt).lower()

    def test_scenario_filtering_logic(self):
        """
        Scenario: User filters data using SELECT IF.
        Expectation: Spec must explicitly mention 'filter' or 'subset'.
        """
        print("\n🧪 Scenario: SPSS Filtering (SELECT IF)...")
        spss = "SELECT IF (age >= 18 AND status = 'Active')."
        
        spec = self.analyze_spss(spss)
        print(f"   [Spec Snippet]: {spec[:100]}...")
        
        self.assertTrue("filter" in spec or "subset" in spec or "select" in spec, 
                        "❌ Analyst failed to describe the filtering logic.")
        self.assertIn("18", spec)
        self.assertIn("active", spec)

    def test_scenario_recoding(self):
        """
        Scenario: User recodes a variable.
        Expectation: Spec must describe the mapping rules.
        """
        print("\n🧪 Scenario: SPSS Recoding (RECODE)...")
        spss = """
        RECODE gender (1 = 'Male') (2 = 'Female') INTO gender_label.
        EXECUTE.
        """
        
        spec = self.analyze_spss(spss)
        print(f"   [Spec Snippet]: {spec[:100]}...")
        
        self.assertIn("male", spec)
        self.assertIn("female", spec)
        self.assertTrue("map" in spec or "convert" in spec or "recode" in spec,
                        "❌ Analyst failed to describe the recoding transformation.")

    def test_scenario_aggregation(self):
        """
        Scenario: User aggregates data (creating a summary).
        Expectation: Spec must mention grouping or summarizing.
        """
        print("\n🧪 Scenario: SPSS Aggregation (AGGREGATE)...")
        spss = """
        AGGREGATE
          /OUTFILE=* MODE=ADDVARIABLES
          /BREAK=region
          /avg_income = MEAN(income).
        """
        
        spec = self.analyze_spss(spss)
        print(f"   [Spec Snippet]: {spec[:100]}...")
        
        self.assertTrue("group" in spec or "break" in spec or "by region" in spec,
                        "❌ Analyst missed the 'Grouping' logic.")
        self.assertTrue("mean" in spec or "average" in spec,
                        "❌ Analyst missed the 'Mean' calculation.")

    def test_scenario_conditional_logic(self):
        """
        Scenario: Complex DO IF / ELSE logic.
        Expectation: Spec must capture the conditional flow.
        """
        print("\n🧪 Scenario: SPSS Conditional Logic (DO IF)...")
        spss = """
        DO IF (score > 90).
           COMPUTE grade = 'A'.
        ELSE IF (score > 80).
           COMPUTE grade = 'B'.
        ELSE.
           COMPUTE grade = 'C'.
        END IF.
        """
        
        spec = self.analyze_spss(spss)
        print(f"   [Spec Snippet]: {spec[:100]}...")
        
        self.assertIn("90", spec)
        self.assertIn("grade", spec)
        self.assertTrue("if" in spec or "when" in spec,
                        "❌ Analyst failed to describe the conditional logic.")

if __name__ == "__main__":
    unittest.main()