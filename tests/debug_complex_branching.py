import sys
import os
from unittest.mock import patch
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.doc_generator import DocumentationEngine

def debug_branching():
    print("🔬 DEBUGGING COMPLEX BRANCHING DIAGRAMS")
    engine = DocumentationEngine()
    
    # Mock LLM Response with explicit targets (Col 4)
    # Notice: 'CheckRegion' points to BOTH 'NorthBranch' AND 'SouthBranch'
    mock_response = """
    Start       | Start Process        | Data  | CheckRegion
    CheckRegion | Region == North?     | Logic | NorthBranch, SouthBranch
    NorthBranch | Tax = 15%            | Logic | Save
    SouthBranch | Tax = 10%            | Logic | Save
    Save        | Save Database        | End   | 
    """
    
    with patch('src.specs.doc_generator.get_ollama_response', return_value=mock_response):
        mermaid = engine.generate_diagram("fake_code", "Test Branching")
    
    print("\n--- GENERATED MERMAID SCRIPT ---")
    print(mermaid)
    print("--------------------------------")
    
    if "CheckRegion --> NorthBranch" in mermaid and "CheckRegion --> SouthBranch" in mermaid:
        print("\n✅ SUCCESS: Branching detected!")
        # 
    else:
        print("\n❌ FAILURE: Nodes are not connected correctly.")

if __name__ == "__main__":
    debug_branching()