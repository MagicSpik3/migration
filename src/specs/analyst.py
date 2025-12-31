import os
import re
import json
from src.specs.prompts import ANALYST_PROMPT
from src.utils.ollama_client import get_ollama_response

class SpecAnalyst: # <--- Renamed back from 'Analyst' to match run_migration.py
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = manifest_path

    def load_manifest(self):
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def _extract_file_references(self, sps_content):
        """
        Scans SPSS content for GET DATA /FILE='...' commands.
        """
        # Finds /FILE='name.csv' or /FILE="name.csv" (Case insensitive)
        pattern = r"(?i)/FILE\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, sps_content)
        return sorted(list(set(matches)))

    def analyze_file(self, entry):
        print(f"Analyzing {entry['legacy_name']} -> {os.path.basename(entry['spec_file'])}...")
        
        # 1. Read Legacy Code
        try:
            with open(entry['legacy_file'], 'r', errors='replace') as f:
                code = f.read()
        except Exception as e:
            print(f"⚠️  Read Error: {e}")
            return

        # 2. Smart Context Injection
        detected_files = self._extract_file_references(code)
        files_context = ", ".join(detected_files) if detected_files else "None detected"
        
        # Prepend context to code so LLM sees it
        enhanced_code_context = f"// [SYSTEM DETECTED INPUT FILES: {files_context}]\n\n{code}"

        # 3. Prepare Prompt
        try:
            prompt = ANALYST_PROMPT.format(
                filename=entry['legacy_name'], 
                spss_code=enhanced_code_context
            )
        except KeyError as e:
            print(f"❌ Prompt Format Error: {e}")
            prompt = f"Analyze this SPSS code: {code}"

        # 4. Call LLM
        spec_content = get_ollama_response(prompt)

        # 5. Save Spec
        os.makedirs(os.path.dirname(entry['spec_file']), exist_ok=True)
        with open(entry['spec_file'], 'w') as f:
            f.write(spec_content)
            
        print(f"   ✅ Spec saved to {entry['spec_file']}")

    def run(self):
        print(f"--- Running Analyst on files from Manifest ---")
        manifest = self.load_manifest()
        
        logic_files = [e for e in manifest if e.get('role') == 'logic']
        
        print(f"--- Running Analyst on {len(logic_files)} files from Manifest ---")
        for entry in logic_files:
            self.analyze_file(entry)