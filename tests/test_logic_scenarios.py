import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response # <--- CALL LLM DIRECTLY
from src.specs.prompts import ARCHITECT_PROMPT

class TestLogicScenarios(unittest.TestCase):

    def generate_code_from_spec(self, spec, schema):
        """
        Helper: Simulates the Architect generating code from a requirement.
        We DO NOT use RefiningAgent here because we are creating from scratch.
        """
        
        # 1. Construct the Prompt (Same as RArchitect)
        full_prompt = ARCHITECT_PROMPT.format(
            target_name="test_logic_function",
            spec_content=spec,
            columns=schema,
            glossary="No specific glossary terms."
        )
        
        # 2. Call LLM Direct (Simulate Generation Phase)
        print("   [Thinking] Asking LLM to Architect...")
        raw_response = get_ollama_response(full_prompt)
        
        # 3. Clean Markdown (Same as RArchitect)
        if "```r" in raw_response: 
            return raw_response.split("```r")[1].split("```")[0].strip()
        elif "```" in raw_response: 
            return raw_response.split("```")[1].split("```")[0].strip()
        return raw_response.strip()

    def test_scenario_column_persistence(self):
        """
        Scenario: The user wants to calculate a simple value.
        Risk: The AI uses 'transmute' or 'select' and drops the other columns.
        Expectation: Code must use 'mutate' and keep unused columns.
        """
        print("\n🧪 Scenario: Column Persistence (Avoiding 'transmute')...")
        
        spec = "Calculate 'bmi' as weight divided by height squared."
        schema = "`id`, `weight`, `height`, `age`, `region`, `irrelevant_col`"
        
        code = self.generate_code_from_spec(spec, schema)
        print(f"   [Output]: {code.replace(chr(10), ' ')[:80]}...")

        # 1. MUST use mutate
        self.assertIn("mutate(", code)
        
        # 2. MUST NOT use transmute (The specific bug we fought)
        self.assertNotIn("transmute", code, "❌ Architect used 'transmute' - this will drop columns!")
        
        # 3. MUST NOT select specific columns (implies dropping others)
        self.assertNotIn("select(", code, "❌ Architect used 'select' - risky for column persistence.") 

    def test_scenario_date_diff(self):
        """
        Scenario: The user wants to calculate a duration.
        Risk: AI uses 'end - start'.
        Expectation: Code must use 'difftime'.
        """
        print("\n🧪 Scenario: Date Math Safety...")
        
        spec = "Calculate 'los' (Length of Stay) as date_discharge minus date_admission."
        schema = "`id`, `date_admission`, `date_discharge`"
        
        code = self.generate_code_from_spec(spec, schema)
        print(f"   [Output]: {code.replace(chr(10), ' ')[:80]}...")

        # 1. Check for difftime
        self.assertIn("difftime", code, "❌ Architect failed to use 'difftime' for date math.")
        self.assertIn('units = "days"', code)

    def test_scenario_aggregation_safety(self):
        """
        Scenario: Flag rows based on a group average.
        Risk: AI uses 'summarise' which collapses the dataframe, losing individual rows.
        Expectation: Code must use 'group_by' + 'mutate'.
        """
        print("\n🧪 Scenario: Aggregation Safety (Window Functions)...")
        
        spec = "Create a flag 'high_cost' if 'cost' is greater than the average cost for that 'region'."
        schema = "`id`, `region`, `cost`"
        
        code = self.generate_code_from_spec(spec, schema)
        print(f"   [Output]: {code.replace(chr(10), ' ')[:80]}...")

        # 1. Must Group
        self.assertIn("group_by(region)", code)
        
        # 2. Must Mutate (Window function) NOT Summarise (Collapse)
        self.assertIn("mutate(", code)
        self.assertNotIn("summarise(", code, "❌ Architect used 'summarise' for a flagging operation. Rows lost!")

if __name__ == "__main__":
    unittest.main()