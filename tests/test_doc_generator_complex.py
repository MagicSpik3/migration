import unittest
import os
import sys
import shutil
import textwrap
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.specs.doc_generator import DocumentationEngine

class TestDocGeneratorComplex(unittest.TestCase):

    def setUp(self):
        # Setup temporary directory for test outputs
        self.test_dir = "temp_docs_test"
        self.docs_dir = os.path.join(self.test_dir, "docs")
        self.repo_root = os.path.join(self.test_dir, "repo")
        
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.repo_root, exist_ok=True)
        
        # Create a mock manifest
        self.manifest_path = os.path.join(self.test_dir, "migration_manifest.json")
        self.spss_file = os.path.join(self.repo_root, "complex_logic.sps")
        
        # Write dummy SPSS file (Complex Branching Logic)
        with open(self.spss_file, 'w') as f:
            f.write("""
            * Complex Branching Logic.
            DO IF (Region = 'North').
               COMPUTE Tax = 0.15.
               IF (Income > 50000) Tax = 0.20.
            ELSE IF (Region = 'South').
               COMPUTE Tax = 0.10.
            ELSE.
               COMPUTE Tax = 0.05.
            END IF.
            EXECUTE.
            """)

        # Write manifest pointing to it
        import json
        with open(self.manifest_path, 'w') as f:
            json.dump([{
                "r_function_name": "calculate_tax",
                "original_spss": "repo/complex_logic.sps",
                "r_file": "src/logic/calculate_tax.R"
            }], f)

        # Initialize Engine with test paths
        self.engine = DocumentationEngine(self.manifest_path)
        # Override directories to point to temp test folder
        self.engine.repo_root = self.test_dir
        self.engine.docs_dir = self.docs_dir

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('src.specs.doc_generator.get_ollama_response')
    def test_complex_branching_diagram(self, mock_llm):
        """
        Scenario: The LLM returns a list of nodes representing a branching flow.
        We verify the system parses this into valid Mermaid syntax without crashing.
        """
        print("\n🧪 Test: Complex Branching Diagram Generation...")
        
        # Mock 1: Summary Text
        summary_text = "Calculates tax based on Region and Income tiers."
        
        # Mock 2: Flowchart Text (Simulating what LLM returns for branching)
        flow_response = """
        Start | Start Process | Input
        CheckRegion | Check Region (North/South) | Logic
        NorthBranch | Set Tax 15% | Logic
        HighIncomeCheck | Check Income > 50k | Logic
        SouthBranch | Set Tax 10% | Logic
        DefaultBranch | Set Tax 5% | Logic
        End | Save Data | End
        """
        
        # Configure the mock to return Summary first, then Flowchart
        mock_llm.side_effect = [summary_text, flow_response]

        # Run the generator
        self.engine.run()

        # Validation
        doc_path = os.path.join(self.docs_dir, "calculate_tax.md")
        self.assertTrue(os.path.exists(doc_path), "Documentation file was not created.")

        with open(doc_path, 'r') as f:
            content = f.read()

        # Check for Mermaid Block
        self.assertIn("```mermaid", content)
        self.assertIn("graph TD;", content)
        
        # Check Nodes exist
        # FIX: Expect Rhombus {} because the ID contains "Check"
        self.assertIn('CheckRegion{"Check Region (North/South)"}', content)
        
        # Check standard logic node
        self.assertIn('NorthBranch["Set Tax 15%"]', content)
        
        # Check Styling Classes applied
        self.assertIn("class Start data;", content)
        self.assertIn("class CheckRegion logic;", content)

        print("   ✅ Branching logic nodes parsed successfully.")

    @patch('src.specs.doc_generator.get_ollama_response')
    def test_markdown_formatting_dedent(self, mock_llm):
        """
        Scenario: Verify that the generated Markdown is flush-left (no indentation bug).
        """
        print("\n🧪 Test: Markdown Indentation/Formatting...")
        
        mock_llm.side_effect = ["Summary line.", "Start | Start | Input\nEnd | End | End"]
        
        self.engine.run()
        
        doc_path = os.path.join(self.docs_dir, "calculate_tax.md")
        with open(doc_path, 'r') as f:
            lines = f.readlines()

        # Check the first meaningful line (The Header)
        # It should NOT start with spaces.
        header_line = lines[0]
        print(f"   [Header Line]: '{header_line.rstrip()}'")
        
        self.assertTrue(header_line.startswith("# Documentation:"), 
                        f"❌ formatting bug detected! Line starts with whitespace: {repr(header_line)}")
        
        # Check that mermaid block is also clean
        mermaid_start = next(line for line in lines if "```mermaid" in line)
        self.assertTrue(mermaid_start.startswith("```mermaid"), 
                        "❌ Mermaid block is indented unexpectedly.")

    @patch('src.specs.doc_generator.get_ollama_response')
    def test_malformed_llm_response(self, mock_llm):
        """
        Scenario: LLM returns garbage or empty string. System should default to placeholder or skip gracefully.
        """
        print("\n🧪 Test: Resilience to Malformed LLM Output...")
        
        # Mock: Valid Summary, but None (Timeout) for Diagram
        mock_llm.side_effect = ["Valid Summary", None]
        
        try:
            self.engine.run()
        except Exception as e:
            self.fail(f"Engine crashed on NULL response: {e}")

        doc_path = os.path.join(self.docs_dir, "calculate_tax.md")
        with open(doc_path, 'r') as f:
            content = f.read()
            
        # Should contain error node in Mermaid
        self.assertIn('Error["LLM Generation Timed Out"]', content)
        print("   ✅ Gracefully handled LLM timeout.")

if __name__ == "__main__":
    unittest.main()