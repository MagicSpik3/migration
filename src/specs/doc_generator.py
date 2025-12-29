import sys
import os
import textwrap # <--- NEW IMPORT

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import json
from src.utils.ollama_client import get_ollama_response
from src.utils.mermaid import MermaidBuilder
from src.specs.prompts import DOC_SUMMARY_PROMPT, DOC_FLOW_PROMPT

class DocumentationEngine:
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
             self.manifest_path = os.path.join(os.getcwd(), "migration_manifest.json")
            
        self.repo_root = os.path.dirname(self.manifest_path)
        self.docs_dir = os.path.join(self.repo_root, "docs")
        os.makedirs(self.docs_dir, exist_ok=True)

    def generate_text(self, spss_code):
        prompt = DOC_SUMMARY_PROMPT.format(code=spss_code)
        return get_ollama_response(prompt).strip()

    def generate_diagram(self, spss_code, title):
        prompt = DOC_FLOW_PROMPT.format(code=spss_code)
        response = get_ollama_response(prompt).strip()
        
        mb = MermaidBuilder(title)
        
        lines = response.split('\n')
        node_ids = []
        
        for line in lines:
            if "|" not in line: continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3: continue
            
            nid, label, ntype = parts[0], parts[1], parts[2].lower()
            
            shape = "rect"
            style = "script"
            
            if "input" in ntype or "data" in ntype:
                shape = "db"
                style = "data"
            elif "end" in ntype:
                shape = "round"
                style = "script"
            elif "logic" in ntype:
                shape = "rect"
                style = "logic"
                
            clean_id = mb.add_node(nid, label, shape=shape, style_class=style)
            node_ids.append(clean_id)
            
        for i in range(len(node_ids) - 1):
            mb.add_edge(node_ids[i], node_ids[i+1])
            
        return mb.generate_script()

    def run(self):
        print(f"📚 Starting Documentation Engine...")
        print(f"   📂 Manifest: {self.manifest_path}")
        print(f"   📂 Output:   {self.docs_dir}")
        
        if not os.path.exists(self.manifest_path):
            print("   ❌ Manifest not found! Run migration first.")
            return

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
            
        for entry in manifest:
            func_name = entry.get('r_function_name', 'unnamed_function')
            
            spss_file = (entry.get('legacy_file') or 
                         entry.get('original_spss') or 
                         entry.get('spss_file') or 
                         entry.get('source_path'))
            
            if not spss_file:
                print(f"   ⚠️ Skipping {func_name} (Missing 'legacy_file' key in manifest)")
                continue

            if not os.path.isabs(spss_file):
                spss_file = os.path.join(self.repo_root, spss_file)

            if not os.path.exists(spss_file):
                print(f"   ⚠️ Skipping {func_name} (File not found on disk: {spss_file})")
                continue
                
            print(f"\n   📝 Documenting {func_name}...")
            
            try:
                with open(spss_file, 'r') as f:
                    spss_code = f.read()
                
                summary_text = self.generate_text(spss_code)
                mermaid_code = self.generate_diagram(spss_code, func_name)
                
                # FIX: Use textwrap.dedent so the file starts at column 0
                md_content = textwrap.dedent(f"""\
                    # Documentation: {func_name}

                    ## 1. Executive Summary
                    {summary_text}

                    ## 2. Process Flowchart
                    ```mermaid
                    {mermaid_code}
                    ```

                    ## 3. Original Source
                    * **File:** `{os.path.basename(spss_file)}`
                    * **Migrated To:** `{os.path.basename(entry.get('r_file', 'unknown.R'))}`
                    """)
                
                out_path = os.path.join(self.docs_dir, f"{func_name}.md")
                with open(out_path, 'w') as f:
                    f.write(md_content)
                    
                print(f"      ✅ Saved to docs/{func_name}.md")
                
            except Exception as e:
                print(f"      ❌ Failed to document {func_name}: {e}")

if __name__ == "__main__":
    engine = DocumentationEngine()
    engine.run()