import unittest
import sys
import os
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.specs.doc_generator import DocumentationEngine

class TestDocGeneratorBranching(unittest.TestCase):
    
    @patch('src.specs.doc_generator.get_ollama_response')
    def test_branching_logic_generation(self, mock_llm):
        """
        Scenario: Verify that the 4th column (TargetNodeID) in the LLM response
        correctly creates branching edges in the Mermaid diagram.
        """
        print("\n🧪 Test: Complex Branching Diagram Generation...")
        
        # Setup Output Directory
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        engine = DocumentationEngine()
        
        # Mock LLM Response (Col 4 contains targets)
        mock_response = """
        Start       | Start Process        | Data  | CheckRegion
        CheckRegion | Region == North?     | Logic | NorthBranch, SouthBranch
        NorthBranch | Tax = 15%            | Logic | Save
        SouthBranch | Tax = 10%            | Logic | Save
        Save        | Save Database        | End   | 
        """
        
        mock_llm.return_value = mock_response
        
        mermaid = engine.generate_diagram("fake_code", "Test Branching")
        
        # --- SAVE ARTIFACT AS PREVIEWABLE MARKDOWN ---
        output_file = os.path.join(output_dir, "branching_diagram.md")
        with open(output_file, "w") as f:
            f.write("# Diagram Preview\n")
            f.write("Press `Ctrl + Shift + V` to view this diagram.\n\n")
            f.write("```mermaid\n")
            f.write(mermaid)
            f.write("\n```")
            
        print("\n--- GENERATED MERMAID SCRIPT ---")
        print(mermaid)
        print("--------------------------------")
        print(f"💾 Saved preview to: {output_file}")
        
        # Assertions
        self.assertIn('CheckRegion{"Region == North?"}', mermaid)
        self.assertIn("CheckRegion --> NorthBranch", mermaid)
        self.assertIn("CheckRegion --> SouthBranch", mermaid)
        self.assertIn("NorthBranch --> Save", mermaid)
        self.assertIn("SouthBranch --> Save", mermaid)

if __name__ == "__main__":
    unittest.main()