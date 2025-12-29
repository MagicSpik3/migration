import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import ARCHITECT_PROMPT

class TestArchitectReliability(unittest.TestCase):

    def generate_code(self, spec, schema):
        """Helper to simulate the Architect generation."""
        full_prompt = ARCHITECT_PROMPT.format(
            target_name="reliability_test_func",
            spec_content=spec,
            columns=schema,
            glossary="No specific glossary terms."
        )
        # Deterministic generation
        return get_ollama_response(full_prompt).strip()

    def test_schema_adherence_weird_names(self):
        """
        Scenario: Spec uses standard terms ('start', 'end'), 
                  but Schema has weird legacy names ('t_start_val', 't_end_val').
        Risk: Architect hallucinates 'start' and 'end' columns because they match the spec.
        Expectation: It must use the ACTUAL schema columns.
        """
        print("\n🧪 Test: Schema Adherence (Weird Names)...")
        spec = "Calculate duration as end minus start."
        schema = "`id`, `t_start_val`, `t_end_val`"  # <--- Weird names
        
        code = self.generate_code(spec, schema)
        print(f"   [Output snippet]: {code.replace(chr(10), ' ')[:80]}...")
        
        # It should NOT invent 'start' or 'end' columns as input
        self.assertNotIn("end - start", code, "❌ Architect ignored schema and hallucinated 'end - start'!")
        
        # It SHOULD use the weird names found in schema
        self.assertIn("t_end_val", code)
        self.assertIn("t_start_val", code)

    def test_environment_safety(self):
        """
        Scenario: Spec asks to "Load the config file".
        Risk: Architect writes `setwd("C:/Users/...")` or absolute paths.
        Expectation: No hardcoded paths or working directory changes.
        """
        print("\n🧪 Test: Environment Safety (No setwd/Paths)...")
        spec = "Load the configuration file 'config.csv' and filter the data."
        schema = "`id`, `data`"
        
        code = self.generate_code(spec, schema)
        
        # BAN unsafe environmental changes
        self.assertNotIn("setwd(", code, "❌ Architect tried to change working directory (setwd)!")
        self.assertNotIn("C:/", code, "❌ Architect used hardcoded Windows path!")
        self.assertNotIn("/home/", code, "❌ Architect used hardcoded Linux path!")

    def test_dependency_hygiene(self):
        """
        Scenario: Spec requires a specific package (e.g., 'zoo' for rolling average).
        Risk: Architect puts `library(zoo)` inside the function.
        Expectation: Use `zoo::rollmean`, NOT `library()`.
        """
        print("\n🧪 Test: Dependency Hygiene (No library calls)...")
        spec = "Calculate a 7-day rolling average of 'sales' using the zoo package."
        schema = "`date`, `sales`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output snippet]: {code.replace(chr(10), ' ')[:80]}...")
        
        # BAN library() calls inside functions (Package development best practice)
        self.assertNotIn("library(", code, "❌ Architect used 'library()' inside a function!")
        self.assertNotIn("require(", code, "❌ Architect used 'require()' inside a function!")
        
        # Expect Namespacing
        self.assertIn("zoo::", code, "❌ Architect failed to namespace the external package (zoo::).")

    def test_dangling_group_safety(self):
        """
        Scenario: Spec asks for a grouped calculation.
        Risk: Architect leaves the dataframe grouped, causing bugs downstream.
        Expectation: Must end with `ungroup()` or `.groups = 'drop'`.
        """
        print("\n🧪 Test: Dangling Group Safety...")
        spec = "Calculate the maximum score per region."
        schema = "`id`, `region`, `score`"
        
        code = self.generate_code(spec, schema)
        
        # It must group...
        self.assertIn("group_by", code)
        
        # ...but it must also cleanup!
        has_ungroup = "ungroup" in code
        has_drop = '.groups = "drop"' in code or ".groups = 'drop'" in code
        
        self.assertTrue(has_ungroup or has_drop, 
                        "❌ Architect left a 'Dangling Group'! Missing ungroup() or .groups='drop'.")

if __name__ == "__main__":
    unittest.main()