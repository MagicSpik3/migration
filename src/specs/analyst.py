import os
import re
import json
from src.utils.ollama_client import get_ollama_response

# --- 1. THE AGGRESSIVE PROMPT (Same as before) ---
ANALYST_PROMPT = """
You are a Technical Business Analyst.
Your goal is to extract the **Business Intent**, NOT the Implementation Detail.

### CRITICAL INSTRUCTION: ABSTRACT THE LOGIC
- **Dates:** If SPSS uses math (e.g. `/ 10000`) or substrings (`substr`) to parse dates, DO NOT document the math. Just write: **"Parse variable X as Date (Format: YYYYMMDD)."**
- **Logic:** Focus on the *outcome* (e.g., "Calculate duration in days"), not the steps (e.g., "Subtract seconds, divide by 86400").

### INSTRUCTIONS:
1. **Text Specification:** Define Data Dictionary and High-Level Logic.
2. **Visual Logic (Mermaid):**
   - **MANDATORY SYNTAX:** Quote all labels (e.g., `A["Parse Date"]`).
   - Show the flow of *Intent*, not math.

### SOURCE SPSS CODE:
{spss_code}

### OUTPUT FORMAT:
Provide the Markdown Specification including the Mermaid block.
"""

def repair_mermaid(text):
    """Regex brute-force to ensure Mermaid labels are quoted."""
    text = re.sub(r'\[\s*(?![\("])([^\]]+?)\s*\]', r'["\1"]', text)
    text = re.sub(r'(?<!\{)\{\s*(?!["\{])([^\}]+?)\s*\}(?!\})', r'{"\1"}', text)
    text = re.sub(r'\{\{\s*(?!")([^\}]+?)\s*\}\}', r'{{"\1"}}', text)
    return text

def run_analyst(manifest_path="migration_manifest.json"):
    # Load the Manifest (The Single Source of Truth)
    if not os.path.exists(manifest_path):
        print(f"❌ Manifest not found at {manifest_path}. Run manifest_manager first.")
        return

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"--- Running Analyst on {len(manifest)} files from Manifest ---")

    for entry in manifest:
        legacy_path = entry['legacy_file']
        spec_path = entry['spec_file']
        func_name = entry['r_function_name']
        
        # Skip if legacy file is missing (sanity check)
        if not os.path.exists(legacy_path):
            print(f"⚠️  Skipping {func_name}: Source file not found ({legacy_path})")
            continue

        print(f"Analyzing {entry['legacy_name']} -> {os.path.basename(spec_path)}...")
        
        with open(legacy_path, 'r', errors='ignore') as f:
            code = f.read()
            
        prompt = ANALYST_PROMPT.format(spss_code=code)
        raw_response = get_ollama_response(prompt)
        
        # Apply the safety net
        clean_response = repair_mermaid(raw_response)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(spec_path), exist_ok=True)
        
        with open(spec_path, 'w') as f:
            f.write(clean_response)
            
        print(f"✅ Spec saved to {spec_path}")

if __name__ == "__main__":
    # Assuming manifest is in the root of the repo relative to this script execution
    # or passed as an argument. For this setup:
    MANIFEST_PATH = os.path.abspath("migration_manifest.json")
    
    # If not found there, try the dummy repo location hardcoded
    if not os.path.exists(MANIFEST_PATH):
        MANIFEST_PATH = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
        
    run_analyst(MANIFEST_PATH)