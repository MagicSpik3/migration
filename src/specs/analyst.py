import os
from src.utils.ollama_client import get_ollama_response

ANALYST_PROMPT = """
You are a Technical Business Analyst.
Your goal is to Reverse Engineer legacy SPSS syntax into a modern **Technical Requirements Specification**.

### SOURCE SPSS CODE:
{spss_code}

### INSTRUCTIONS:
Analyze the code and produce a Markdown specification.
Focus on **Business Logic** and **Data Transformations**, ignoring syntax-specific artifacts (like FORMATS or EXECUTE).

### OUTPUT FORMAT (Markdown):

# Specification: [Filename]

## 1. Data Dictionary
| Variable | Type | Description/Format |
| :--- | :--- | :--- |
| dor | String | Date of Registration (Format: YYYYMMDD) |

## 2. Transformation Logic
*Describe every variable created or modified.*
* **Example:** `delay_days` = Calculate days between `dor` and `dod`.

## 3. Filtering & Business Rules
*List any records that are excluded or flagged.*
* **Rule 1:** Exclude records where...

## 4. Key Assumptions / Ambiguities
*Note any logic that seems specific to SPSS idiosyncrasies (e.g. DATEDIF handling).*
"""

def generate_spec(sps_path, output_dir):
    filename = os.path.basename(sps_path).replace('.sps', '.md')
    print(f"Analyzing {filename}...")
    
    with open(sps_path, 'r') as f:
        code = f.read()
        
    prompt = ANALYST_PROMPT.format(spss_code=code)
    spec_md = get_ollama_response(prompt)
    
    out_path = os.path.join(output_dir, filename)
    with open(out_path, 'w') as f:
        f.write(spec_md)
        
    print(f"✅ Spec saved to {out_path}")

if __name__ == "__main__":
    REPO_DIR = os.path.expanduser("~/git/dummy_spss_repo/syntax")
    OUTPUT_DIR = os.path.expanduser("~/git/dummy_spss_repo/specs")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for root, dirs, files in os.walk(REPO_DIR):
        for file in files:
            if file.endswith(".sps"):
                generate_spec(os.path.join(root, file), OUTPUT_DIR)