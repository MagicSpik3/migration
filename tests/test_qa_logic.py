import unittest
from unittest.mock import patch
import os
import sys
import json
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.qa_engineer import QAEngineer

class TestQALogic(unittest.TestCase):

    def setUp(self):
        self.test_dir = "temp_qa_test"
        
        # FIX: Create the 'r_from_spec' subdirectory so path calculation works
        self.r_dir = os.path.join(self.test_dir, "r_from_spec")
        os.makedirs(self.r_dir, exist_ok=True)
        
        # Mock Manifest structure
        self.manifest_path = os.path.join(self.test_dir, "migration_manifest.json")
        self.r_file = os.path.join(self.r_dir, "calc.R") # <--- Inside subdir
        self.spec_file = os.path.join(self.test_dir, "calc.md")
        
        with open(self.manifest_path, 'w') as f:
            json.dump([{
                "r_function_name": "calc_delays",
                "r_file": self.r_file,
                "spec_file": self.spec_file
            }], f)
            
        with open(self.r_file, 'w') as f: f.write("R code")
        with open(self.spec_file, 'w') as f: f.write("Spec")
        
        self.qa = QAEngineer(self.manifest_path)
        self.qa.repo_root = self.test_dir

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('src.specs.qa_engineer.get_ollama_response')
    def test_test_generation_path(self, mock_llm):
        """Does QA Engineer save tests to tests/test_funcname.R?"""
        mock_llm.return_value = "test_that('foo', { expect_equal(1,1) })"
        
        entry = {"r_function_name": "calc_delays", "r_file": self.r_file, "spec_file": self.spec_file}
        
        generated_path = self.qa.generate_tests(entry)
        
        # Expected: temp_qa_test/tests/test_calc_delays.R
        expected_dir = os.path.join(self.test_dir, "tests")
        expected_file = os.path.join(expected_dir, "test_calc_delays.R")
        
        # Debug prints if assertion fails
        print(f"\n   Generated: {generated_path}")
        print(f"   Expected:  {expected_file}")
        
        self.assertEqual(generated_path, expected_file)
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, 'r') as f:
            content = f.read()
            
        self.assertIn("library(testthat)", content)
        self.assertIn("source(", content) # Should source the R file

if __name__ == "__main__":
    unittest.main()