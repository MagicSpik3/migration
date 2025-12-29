import unittest
import os
import shutil
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.qa_engineer import QAEngineer

class TestQALogic(unittest.TestCase):

    def setUp(self):
        self.test_dir = "temp_qa_test"
        
        self.r_dir = os.path.join(self.test_dir, "r_from_spec")
        os.makedirs(self.r_dir, exist_ok=True)
        
        self.manifest_path = os.path.join(self.test_dir, "migration_manifest.json")
        self.r_file = os.path.join(self.r_dir, "calc.R")
        self.spec_file = os.path.join(self.test_dir, "calc.md")
        
        with open(self.manifest_path, 'w') as f:
            json.dump([{
                "r_function_name": "calc_delays",
                "r_file": self.r_file,
                "spec_file": self.spec_file
            }], f)
        
        with open(self.r_file, 'w') as f: f.write("R code")
        with open(self.spec_file, 'w') as f: f.write("Spec")
        
        # FIX: Pass the DIRECTORY
        self.qa = QAEngineer(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_test_generation_path(self):
        """Ensure test files are targeted to the correct directory."""
        print("\n🧪 Test: QA Path Resolution...")
        expected_test_path = os.path.join(self.qa.test_dir, "test_calc_delays.R")
        # We aren't running generation here (too expensive), just checking path logic
        self.assertTrue(self.qa.test_dir.endswith("tests"))
        self.assertTrue(os.path.isdir(self.qa.test_dir))

if __name__ == "__main__":
    unittest.main()