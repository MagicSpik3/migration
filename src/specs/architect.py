import json
import os
import csv
from src.utils.ollama_client import get_ollama_response

# WE USE DOUBLE BRACES {{ }} FOR LITERALS IN THE PROMPT TO PREVENT FORMATTING ERRORS
ARCHITECT_PROMPT = """
You are a Senior R Developer building an R Package. 
Translate the specification into a production-ready R function.

### RULES:
1. **Explicit Namespacing (CRITICAL):**
   - You MUST use double-colon syntax for all non-base functions.
   - ❌ WRONG: `mutate(df, date = ymd(str_sub(x, 1, 4)))`
   - ✅ RIGHT: `dplyr::mutate(df, date = lubridate::ymd(stringr::str_sub(x, 1, 4)))`
   - *Exception:* You may use standard infix operators like `%>%` without `::`.

2. **Pipeline Continuity:**
   - Input: `df` (dataframe)
   - Output: `return(df)` (dataframe)
   - Do NOT use `library()` calls inside the function. Dependencies belong in the package definition.

### DATA SCHEMA (THE TRUTH):
The input `df` contains ONLY these columns:
{columns}
**CRITICAL: DO NOT USE VARIABLES NOT LISTED ABOVE.**

### KNOWLEDGE BASE:
{glossary}

### METADATA:
- **Function Name:** `{target_name}`
- **Specification:**
{spec_content}

### OUTPUT:
Only the R code.
"""

class RArchitect:
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
        self.repo_root = os.path.dirname(os.path.dirname(self.manifest_path))

    def get_schema(self):
        csv_path = os.path.join(self.repo_root, "input_data.csv")
        
        # Test environment fallback
        if not os.path.exists(csv_path):
            if os.path.exists("input_data.csv"):
                 csv_path = "input_data.csv"
            else:
                return "(No input_data.csv found - strictly follow spec)"
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                return ", ".join([f"`{h}`" for h in headers])
        except Exception as e:
            return "(Error reading CSV header)"

    def load_glossary(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        glossary_path = os.path.join(current_dir, "..", "knowledge", "glossary.csv")
        
        if not os.path.exists(glossary_path):
            return "(No glossary found)"
        with open(glossary_path, 'r') as f:
            return f.read()

    def run(self):
        if not os.path.exists(self.manifest_path):
            print(f"❌ Manifest not found at {self.manifest_path}")
            return

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        schema_str = self.get_schema()
        glossary_str = self.load_glossary()
        print(f"📊 Detected Schema: {schema_str}")

        for entry in manifest:
            if entry.get('role') == 'controller': continue
            print(f"🏛️  Architecting {entry['r_function_name']}...")
            
            spec_path = entry['spec_file']
            if not os.path.exists(spec_path): continue
                
            with open(spec_path, 'r') as f: spec_content = f.read()

            try:
                prompt = ARCHITECT_PROMPT.format(
                    target_name=entry['r_function_name'],
                    spec_content=spec_content,
                    columns=schema_str,
                    glossary=glossary_str
                )
            except KeyError: continue
            
            r_code = get_ollama_response(prompt)
            clean_code = r_code.strip()
            if "```r" in clean_code: 
                clean_code = clean_code.split("```r")[1].split("```")[0]
            elif "```" in clean_code: 
                clean_code = clean_code.split("```")[1].split("```")[0]

            target_path = entry['r_file']
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w') as f:
                f.write(clean_code.strip())
            print(f"   ✅ Saved to {target_path}")

if __name__ == "__main__":
    architect = RArchitect()
    architect.run()