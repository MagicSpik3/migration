import unittest
import os
import shutil
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.manifest_manager import ManifestManager

class TestManifest(unittest.TestCase):

    def setUp(self):
        # Create a dummy environment
        self.test_dir = "temp_test_repo"
        os.makedirs(os.path.join(self.test_dir, "syntax"), exist_ok=True)
        
        # Create a dummy SPSS file
        with open(os.path.join(self.test_dir, "syntax", "job1.sps"), "w") as f:
            f.write("GET DATA /FILE='data.csv'.\nEXECUTE.")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists("migration_manifest.json"):
            os.remove("migration_manifest.json")

    def test_manifest_generation(self):
        """Does the Manifest Manager find files and create JSON?"""
        manager = ManifestManager(os.path.join(self.test_dir, "syntax"))
        manager.generate_manifest()
        
        self.assertTrue(os.path.exists("migration_manifest.json"))
        
        with open("migration_manifest.json", "r") as f:
            data = json.load(f)
        
        # Check if job1 was found
        found = any(d['legacy_name'] == 'job1.sps' for d in data)
        self.assertTrue(found, "Manifest failed to index job1.sps")

if __name__ == '__main__':
    unittest.main()