import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the direct client
from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import TEST_GENERATE_CODE_PROMPT

class TestArchitectAdvanced(unittest.TestCase):
    
    def generate_code(self, spec, schema):
        # Helper to simulate architect run
        # FIX: Map the test inputs to the new required PROMPT fields
        prompt = TEST_GENERATE_CODE_PROMPT.format(
            target_name="advanced_test_func", # Dummy function name
            columns=schema,                   # Map 'schema' -> 'columns'
            glossary="No specific glossary terms.", # Dummy glossary
            spec_content=spec                 # Map 'spec' -> 'spec_content'
        )



        response = get_ollama_response(prompt)
        return response

    def test_left_join_logic(self):
        print("\n🧪 Scenario: Joins (Left Join)...")
        spec = "Enrich the main data by joining with the 'demographics' lookup table on 'patient_id'."
        schema = "`patient_id`, `diagnosis_code`"
        code = self.generate_code(spec, schema)
        self.assertIn("left_join", code)

    def test_pivot_longer(self):
        print("\n🧪 Scenario: Reshaping (Pivot Longer)...")
        spec = "Convert the columns 'q1_score', 'q2_score', 'q3_score' into rows defined by 'question' and 'score'."
        schema = "`id`, `q1_score`, `q2_score`, `q3_score`, `region`"
        code = self.generate_code(spec, schema)
        self.assertIn("pivot_longer", code)
        self.assertIn("cols", code)

    def test_complex_case_when(self):
        print("\n🧪 Scenario: Complex Conditional (case_when)...")
        # FIX: Make the logic non-binary (Low/Medium/High) to force case_when
        spec = "Categorize 'risk' as 'High' if age > 60, 'Medium' if bmi > 25, otherwise 'Low'."
        schema = "`id`, `age`, `bmi`"
        code = self.generate_code(spec, schema)
        self.assertIn("case_when", code)
        self.assertIn("High", code)
        self.assertIn("Medium", code)

    def test_string_cleaning(self):
        print("\n🧪 Scenario: String Cleaning (Regex)...")
        spec = "Clean the 'id' column by removing the prefix 'ID-'."
        schema = "`id`, `name`"
        code = self.generate_code(spec, schema)
        
        # Robust Assertion (Accepts stringr OR base R)
        has_stringr = "str_remove" in code or "str_replace" in code
        has_base = "gsub" in code or "sub" in code
        
        if not (has_stringr or has_base):
            print(f"\n❌ FAILED CODE OUTPUT:\n{code}\n")
            
        self.assertTrue(has_stringr or has_base, 
                        "Architect failed to clean string (checked for str_remove, str_replace, gsub, sub).")

if __name__ == "__main__":
    unittest.main()