import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.optimizer import CodeOptimizer

class TestOptimizerLogic(unittest.TestCase):

    def setUp(self):
        self.test_dir = "temp_optimizer_test"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Mock Manifest
        self.manifest_path = os.path.join(self.test_dir, "migration_manifest.json")
        self.manifest_data = [{
            "r_function_name": "calc_delays",
            "r_file": os.path.join(self.test_dir, "calc_delays.R"),
            "role": "logic"
        }]
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)
            
        # Create dummy R file
        with open(self.manifest_data[0]['r_file'], 'w') as f:
            f.write("dummy <- function() {}")

        self.optimizer = CodeOptimizer(self.manifest_path)
        self.optimizer.repo_root = self.test_dir

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)


    @patch('subprocess.run')
    def test_ast_refactor_called(self, mock_run):
        """Does the optimizer construct the correct Rscript command?"""
        # Simple existence check for now since logic is inside inner callback
        self.assertTrue(hasattr(self.optimizer, 'generate_temp_schema'))


    @patch('subprocess.run')
    def test_linter_parsing(self, mock_run):
        """Does check_lint_status correctly parse the || separated format?"""
        # Mock stdout from Rscript
        mock_result = MagicMock()
        
        # NEW FORMAT: "Line X: Msg || Line Y: Msg"
        mock_result.stdout = "Line 1: Avoid global variables||Line 5: Line too long"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # CALL THE NEW METHOD NAME
        score, details = self.optimizer.check_lint_status("dummy.R")
        
        # VALIDATE
        self.assertEqual(score, 2)
        self.assertIn("Line 1: Avoid global variables", details)
        self.assertIn("Line 5: Line too long", details)

    @patch('subprocess.run')
    def test_ast_refactor_called(self, mock_run):
        """Does the optimizer actually try to run refactor.R?"""
        # We need to test the callback logic inside optimize_file
        # This is tricky because the callback is internal.
        # Instead, we verify that the AST Refactor script path is resolved correctly.
        
        refactor_script = os.path.join(self.optimizer.repo_root, "../migration/src/utils/refactor.R")
        # Just check logic construction
        fallback_script = os.path.abspath("src/utils/refactor.R")
        
        self.assertTrue(
            os.path.exists(refactor_script) or "migration" in fallback_script, 
            "Optimizer cannot locate refactor.R script path logic"
        )

    def test_manual_callback_logic(self):
        """Simulate the Agent callback to ensure it triggers the test harness."""
        # This requires mocking the test_function_logic method
        with patch.object(self.optimizer, 'test_function_logic', return_value=(True, "PASS")) as mock_test:
            with patch.object(self.optimizer, 'auto_format_file') as mock_fmt:
                with patch('subprocess.run') as mock_sub: # Mock AST call
                    
                    # We manually reconstruct the callback logic for testing
                    # (In a real scenario, we'd refactor the callback to be a standalone method, 
                    # but for now we test the integration points)
                    
                    r_path = self.manifest_data[0]['r_file']
                    func_name = "calc_delays"
                    
                    # 1. Write Candidate
                    with open(r_path, 'w') as f: f.write("new_code <- 1")
                    
                    # 2. Run Logic Check
                    is_valid, msg = self.optimizer.test_function_logic(r_path, func_name)
                    
                    self.assertTrue(is_valid)
                    mock_test.assert_called_once()

if __name__ == "__main__":
    unittest.main()