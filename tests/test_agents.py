import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import csv
import textwrap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.refining_agent import RefiningAgent
from src.specs.architect import RArchitect
from src.specs.prompts import ARCHITECT_PROMPT 



class TestRefiningAgent(unittest.TestCase):
    def setUp(self):
        self.agent = RefiningAgent("System Prompt")

    def test_code_extraction_markdown(self):
        # 2. Use textwrap.dedent() so the string becomes flush-left
        raw_llm_output = textwrap.dedent("""
        Here is the code:
        ```r
        library(dplyr)
        df <- df %>% filter(id > 0)
        ```
        """)
        
        extracted = self.agent.extract_code(raw_llm_output)
        expected = "library(dplyr)\ndf <- df %>% filter(id > 0)"
        
        self.assertEqual(extracted.strip(), expected)



    def test_code_extraction_heuristic(self):
        raw_llm_output = """
        calc_delays <- function(df) {
            return(df)
        }
        """
        extracted = self.agent.extract_code(raw_llm_output)
        self.assertIn("calc_delays <- function(df)", extracted)

class TestArchitect(unittest.TestCase):
    def setUp(self):
        # Create a temporary dummy repo structure
        self.test_dir = "temp_architect_test"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a dummy Manifest (required by Architect init)
        with open(os.path.join(self.test_dir, "migration_manifest.json"), "w") as f:
            f.write("[]")

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_prompt_formatting(self):
        """Does the ARCHITECT_PROMPT crash when formatted?"""
        try:
            formatted = ARCHITECT_PROMPT.format(
                target_name="test_func",
                spec_content="Calculate stuff",
                columns="`id`, `age`", # Simulated Schema
                glossary="filter -> filter"
            )
        except KeyError as e:
            self.fail(f"Architect Prompt formatting failed! Error: {e}")

        self.assertIn("test_func", formatted)
        self.assertIn("`id`, `age`", formatted)

    def test_schema_reading_logic(self):
        """Does get_schema() actually read the CSV headers?"""
        # 1. Create a dummy CSV in the 'repo root' (one level up from manifest)
        # Structure: temp_architect_test/migration_manifest.json
        #            input_data.csv (should be here relative to manifest location logic)
        
        # The Architect derives repo_root as os.path.dirname(os.path.dirname(manifest_path))
        # So we need to mimic that structure or mock the path.
        
        # Let's mock the internal method to use our temp file
        csv_path = os.path.join(self.test_dir, "input_data.csv")
        with open(csv_path, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "date_of_birth", "status"]) # The Headers
            writer.writerow(["101", "2020-01-01", "Active"])

        architect = RArchitect(os.path.join(self.test_dir, "migration_manifest.json"))
        
        # Force the repo_root to be our test dir for this unit test
        architect.repo_root = self.test_dir
        
        schema = architect.get_schema()
        
        print(f"\n   [DEBUG] Read Schema: {schema}")
        
        self.assertIn("`user_id`", schema)
        self.assertIn("`date_of_birth`", schema)
        self.assertIn("`status`", schema)

if __name__ == '__main__':
    unittest.main()