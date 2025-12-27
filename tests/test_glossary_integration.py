import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# FIX: Import the direct client, not the Agent
from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import ARCHITECT_PROMPT

class TestGlossaryIntegration(unittest.TestCase):

    def generate_with_glossary(self, spec, glossary_content):
        """Simulate Architect with a specific injected Glossary."""
        
        full_prompt = ARCHITECT_PROMPT.format(
            target_name="glossary_test_func",
            spec_content=spec,
            columns="`id`, `revenue`, `cost`, `var_x`",
            glossary=glossary_content # <--- INJECTING KNOWLEDGE HERE
        )
        
        # FIX: Call LLM directly (Generation Mode), don't use RefiningAgent
        print("   [Thinking] Asking LLM to Architect with Glossary...")
        raw_response = get_ollama_response(full_prompt)

        # Clean Markdown
        if "```r" in raw_response: 
            return raw_response.split("```r")[1].split("```")[0].strip()
        elif "```" in raw_response: 
            return raw_response.split("```")[1].split("```")[0].strip()
        return raw_response.strip()

    def test_glossary_definition_override(self):
        """
        Scenario: The spec asks for 'Profit'. 
        Standard AI assumption: Revenue - Cost.
        Glossary Definition: (Revenue - Cost) * 0.8 (Tax deduction).
        Expectation: AI must use the Glossary formula.
        """
        print("\n🧪 Scenario: Glossary Logic Injection...")
        
        spec = "Calculate the final profit for the quarter."
        glossary = "Profit: Defined as (revenue - cost) * 0.8 to account for 20% tax."
        
        code = self.generate_with_glossary(spec, glossary)
        print(f"   [Output Snippet]: {code.replace(chr(10), ' ')[:80]}...")
        
        # It must include the tax multiplier found ONLY in the glossary
        self.assertIn("0.8", code, "❌ Architect ignored the Glossary definition for Profit!")
        self.assertIn("revenue", code)
        self.assertIn("cost", code)

    def test_glossary_variable_renaming(self):
        """
        Scenario: The input data has cryptic names (var_x).
        Glossary: var_x = 'patient_status'.
        Expectation: The code should rename the column or use a clear alias.
        """
        print("\n🧪 Scenario: Glossary Variable Renaming...")
        
        spec = "Filter the data to keep only active patients."
        glossary = "var_x: Represents 'patient_status'. '1' means Active."
        
        code = self.generate_with_glossary(spec, glossary)
        print(f"   [Output Snippet]: {code.replace(chr(10), ' ')[:80]}...")
        
        # It should know that var_x is the column to filter on
        self.assertIn("var_x", code, "❌ Architect didn't link 'active patients' to 'var_x'.")
        # It should know that '1' is the value for Active
        self.assertIn("1", code, "❌ Architect didn't use the Glossary value for 'Active'.")

if __name__ == "__main__":
    unittest.main()