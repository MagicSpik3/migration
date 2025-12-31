import os
import json
from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import REFACTOR_PROMPT


def run_refactorer(manifest_path="migration_manifest.json"): 
    manifest_path = os.path.abspath(manifest_path) 
    if not os.path.exists(manifest_path): 
        manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"--- Refactoring Logic Functions ---")
    for entry in manifest:
        if entry.get('role') == 'controller': continue

        r_path = entry['r_file']
        func_name = entry['r_function_name']
        
        if not os.path.exists(r_path): continue

        print(f"🔧 Polishing {func_name}...")
        with open(r_path, 'r') as f:
            draft_code = f.read()

        prompt = REFACTOR_PROMPT.format(r_code=draft_code, func_name=func_name)
        clean_code = get_ollama_response(prompt)
        
        # Strip Markdown
        if "```r" in clean_code: clean_code = clean_code.split("```r")[1].split("```")[0]
        elif "```" in clean_code: clean_code = clean_code.split("```")[1].split("```")[0]

        with open(r_path, 'w') as f:
            f.write(clean_code.strip())
            
        print(f"   ✨ Code is now Idiomatic.")
if __name__ == "__main__": run_refactorer()        
