import sys
import os
import shutil
import textwrap
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.specs.doc_generator import DocumentationEngine

def visualize_complex_doc():
    print("🔬 VISUALIZING COMPLEX DOC GENERATION")
    print("====================================")
    
    # 1. Setup: Use the REAL docs directory so you can see the file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    manifest_path = os.path.join(project_root, "migration_manifest.json")
    
    # We will "trick" the engine into documenting a fake file without messing up your real manifest
    engine = DocumentationEngine(manifest_path)
    
    # 2. Mock Data (The "Complex Branching" Scenario)
    fake_spss_code = "DO IF (Region='North')..."
    func_name = "demo_complex_logic"
    
    summary_text = "Calculates tax based on Region and Income tiers (North=15%, South=10%, Others=5%)."
    
    # The Mermaid nodes the LLM 'returns'
    flow_response = """
    Start | Start Process | Input
    CheckRegion | Check Region (North/South) | Logic
    NorthBranch | Set Tax 15% | Logic
    HighIncomeCheck | Check Income > 50k | Logic
    SouthBranch | Set Tax 10% | Logic
    DefaultBranch | Set Tax 5% | Logic
    End | Save Data | End
    """

    # 3. Manually Trigger the Generation (Bypassing the file reader loop)
    print(f"   📝 Generating {func_name}.md ...")
    
    mermaid_code = engine.generate_diagram(fake_spss_code, func_name)
    # We cheat and inject our mock response into the diagram generator? 
    # Actually, we can't easily mock inside a script without `unittest.mock` context managers or monkeypatching.
    # Let's monkeypatch specifically for this run.
    
    with patch('src.specs.doc_generator.get_ollama_response') as mock_llm:
        mock_llm.side_effect = [summary_text, flow_response]
        
        # Call the internal methods manually to verify the flow
        summary = engine.generate_text(fake_spss_code)
        mermaid = engine.generate_diagram(fake_spss_code, func_name)
        
        # Construct the final markdown using the SAME template logic as the class
        md_template = textwrap.dedent("""\
            # Documentation: {func_name}

            ## 1. Executive Summary
            {summary_text}

            ## 2. Process Flowchart
            ```mermaid
            {mermaid_code}
            ```

            ## 3. Original Source
            * **File:** `demo_script.sps`
            * **Migrated To:** `demo_script.R`
            """)
        
        content = md_template.format(
            func_name=func_name,
            summary_text=summary,
            mermaid_code=mermaid
        )

    # 4. Save and Print
    output_path = os.path.join(engine.docs_dir, f"{func_name}.md")
    with open(output_path, 'w') as f:
        f.write(content)

    print(f"   ✅ Saved file to: {output_path}")
    print("\n--- [FILE CONTENT PREVIEW] ---")
    print(content)
    print("------------------------------")

if __name__ == "__main__":
    visualize_complex_doc()