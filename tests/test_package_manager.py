import unittest
import os
import shutil
from src.specs.package_manager import PackageManager

class TestPackageManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_pkg_test"
        self.r_dir = os.path.join(self.test_dir, "r_from_spec")
        os.makedirs(self.r_dir, exist_ok=True)
        self.pm = PackageManager(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_dependency_scan(self):
        """Does it find pkg::func calls?"""
        # Create a dummy file using stringr and lubridate
        with open(os.path.join(self.r_dir, "test.R"), "w") as f:
            f.write("x <- stringr::str_sub(y)\nz <- lubridate::ymd(w)\n")
            
        deps = self.pm.scan_dependencies()
        self.assertIn("stringr", deps)
        self.assertIn("lubridate", deps)
        self.assertIn("dplyr", deps) # Default

    def test_description_generation(self):
        """Does it create a valid DESCRIPTION file?"""
        # Create dummy file
        with open(os.path.join(self.r_dir, "test.R"), "w") as f:
            f.write("x <- zoo::rollmean(y)")
            
        self.pm.generate_description()
        
        desc_path = os.path.join(self.test_dir, "DESCRIPTION")
        self.assertTrue(os.path.exists(desc_path))
        
        with open(desc_path, "r") as f:
            content = f.read()
            
        self.assertIn("Package: migrationRepo", content)
        self.assertIn("zoo", content)
        self.assertIn("Imports:", content)

if __name__ == "__main__":
    unittest.main()