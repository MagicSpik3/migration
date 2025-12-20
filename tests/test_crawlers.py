import unittest
import tempfile
import os
import json
from src.crawlers.r_crawler import parse_r_file, crawl_and_parse

# --- Test Data: A snippet of R code ---
# We intentionally include tricky things like nested braces and comments
SAMPLE_R_CODE = """
# This is a comment
my_function <- function(arg1, arg2 = "default") {
    if (arg1 > 0) {
        print("Nested brace")
    }
    return(arg2)
}

another_func <- function() {
    # Empty function
}
"""

class TestRCrawler(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory and R file before each test."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.r_file_path = os.path.join(self.test_dir.name, "test_script.R")
        
        with open(self.r_file_path, 'w') as f:
            f.write(SAMPLE_R_CODE)

    def tearDown(self):
        """Cleanup after test."""
        self.test_dir.cleanup()

    def test_parse_single_file(self):
        """Test if the parser correctly identifies functions and arguments."""
        functions = parse_r_file(self.r_file_path)
        
        # Check we found 2 functions
        self.assertEqual(len(functions), 2)
        
        # Verify first function details
        func1 = functions[0]
        self.assertEqual(func1['function_name'], "my_function")
        self.assertIn("arg1", func1['variables'])
        # It should detect arguments before the default value assignment
        self.assertIn("arg2", func1['variables'])
        
        # Verify content capture (simple check)
        self.assertIn('print("Nested brace")', func1['code_chunk'])

    def test_brace_counting_logic(self):
        """Ensure the parser handles nested braces correctly."""
        functions = parse_r_file(self.r_file_path)
        func1 = functions[0]
        
        # The chunk should include the closing brace of the function
        self.assertTrue(func1['code_chunk'].strip().endswith("}"))
        
        # It should NOT include the start of the next function
        self.assertNotIn("another_func", func1['code_chunk'])

    def test_crawl_directory(self):
        """Test the full directory crawl logic."""
        output_json = os.path.join(self.test_dir.name, "output.json")
        
        # Run the full crawler
        crawl_and_parse(self.test_dir.name, output_json)
        
        # Check if JSON file was created
        self.assertTrue(os.path.exists(output_json))
        
        # Check JSON content
        with open(output_json, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['repo_name'], os.path.basename(self.test_dir.name))

if __name__ == '__main__':
    unittest.main()