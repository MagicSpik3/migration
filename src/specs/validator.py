import os
import json
from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import VALIDATOR_PROMPT

class CodeValidator:
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")

    def validate_file(self, entry):
        r_path = entry['r_file']
        spss_path = entry['legacy_file'] # Ensure this key exists in your manifest logic, or derive it
        
        # Fallback if manifest doesn't have absolute path to legacy file
        if not spss_path or not os.path.exists(spss_path):
            # Try to guess based on syntax dir
            spss_path = r_path.replace("r_from_spec", "syntax").replace(".R", ".sps")

        if not os.path.exists(r_path): return False
        
        print(f"🧐 Validating logic for {entry['r_function_name']}...")
        
        with open(r_path, 'r') as f: r_code = f.read()
        
        if os.path.exists(spss_path):
            with open(spss_path, 'r', errors='ignore') as f: spss_code = f.read()
        else:
            spss_code = "(Source SPSS not found)"
        
        prompt = VALIDATOR_PROMPT.format(spss_code=spss_code, r_code=r_code)
        response = get_ollama_response(prompt).strip()
        
        if "PASS" in response:
            print(f"   ✅ Logic Approved.")
            return True
        else:
            reason = response.replace("FAIL:", "").strip().split("\n")[0]
            print(f"   🛑 Logic Rejection: {reason}")
            return False

    def run(self):
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
            
        all_passed = True
        for entry in manifest:
            if entry.get('role') == 'controller': continue
            if not self.validate_file(entry):
                all_passed = False
                
        return all_passed



if __name__ == "__main__":
    validator = CodeValidator()
    validator.run()

