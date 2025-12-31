import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.specs.prompts import EXTRACT_GRAPH_COMPONENTS_PROMPT, STAKEHOLDER_DOCS_PROMPT
from src.utils.ollama_client import get_ollama_response
from src.utils.mermaid import MermaidBuilder

class TestStakeholderDocs(unittest.TestCase):

    def test_mermaid_builder_syntax(self):
        """
        Unit Test: Verify the MermaidBuilder produces valid syntax.
        """
        print("\n🧪 Testing Mermaid Builder Module...")
        mb = MermaidBuilder("Test Flow")
        n1 = mb.add_node("step1", "Load Data", shape="db", style_class="data")
        n2 = mb.add_node("step2", "Filter Rows", shape="rect", style_class="logic")
        mb.add_edge(n1, n2, "On Success")
        
        output = mb.generate_script()
        print(f"   [Mermaid Output]:\n{output[:100]}...")
        
        self.assertIn("graph TD;", output)
        self.assertIn("step1[", output) # Database shape logic check
        self.assertIn("-->", output)
        self.assertIn("classDef data", output)

    def test_analyst_plain_english_translation(self):
        """
        Scenario: Stakeholder needs to understand 'AGGREGATE /BREAK=Region'.
        Expectation: Output must be simple English, no code keywords.
        """
        print("\n🧪 Scenario: Analyst Translation (Readability)...")
        
        spss_code = """
        AGGREGATE
          /OUTFILE=* MODE=ADDVARIABLES
          /BREAK=Region
          /Sales_Mean = MEAN(Sales).
        """
        
        prompt = STAKEHOLDER_DOCS_PROMPT.format(code=spss_code)


        explanation = get_ollama_response(prompt).strip()
        print(f"   [Explanation]: {explanation}")
        
        # Quality Checks
        self.assertNotIn("AGGREGATE", explanation.upper(), "❌ Explanation contained technical jargon.")
        self.assertTrue("average" in explanation.lower() or "mean" in explanation.lower(), 
                        "❌ Explanation missed the core math concept.")
        self.assertTrue("region" in explanation.lower(), 
                        "❌ Explanation missed the grouping concept.")

    def test_visual_generation_flow(self):
        """
        Scenario: Convert a Logic Spec into a Diagram Structure.
        We ask the LLM to identify the 'Nodes' and 'Edges' from a story,
        then use our Builder to render it.
        """
        print("\n🧪 Scenario: Automated Diagram Generation...")
        
        spec = """
        1. Load the 'Patient_Data.csv' file.
        2. Filter for patients with status 'Active'.
        3. If Age > 65, label as 'Senior', otherwise 'Adult'.
        4. Save the result to 'Analysis_Ready.csv'.
        """
        
        # 1. Ask LLM to extract graph components (Structured Data Extraction)
        prompt = EXTRACT_GRAPH_COMPONENTS_PROMPT.format(code=spec)

                
        response = get_ollama_response(prompt)
        print(f"   [LLM Extraction]:\n{response}")
        
        # 2. Simulate parsing the response into the Builder
        # (In a real app, you'd have a robust parser here, we verify the concept)
        mb = MermaidBuilder()
        
        # Naive parsing for the test
        lines = response.split('\n')
        nodes_created = []
        for line in lines:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    nid = mb.add_node(parts[0], parts[1], shape="rect")
                    nodes_created.append(nid)
        
        # Link them sequentially
        for i in range(len(nodes_created) - 1):
            mb.add_edge(nodes_created[i], nodes_created[i+1])
            
        diagram = mb.generate_script()
        
        # 3. Verify the Diagram reflects the Story
        self.assertIn("Load", diagram)
        self.assertIn("Filter", diagram)
        self.assertIn("Save", diagram)
        self.assertIn("-->", diagram)

if __name__ == "__main__":
    unittest.main()