import json
import os
from src.utils.ollama_client import get_ollama_response

ARCHITECT_PROMPT = """
You are a Senior R Developer. 
Implement the R function strictly according to these constraints.

### METADATA:
- **Function Name:** `{target_name}`
- **Input:** `df` (Dataframe)
- **Output:** `df` (Dataframe)

### CODING RULES (CRITICAL):
1. **Date Parsing:**
   - Use `lubridate::ymd()` directly on the column.
   - ❌ WRONG: `ymd(paste0(substr(col, 1, 4), ...))`
   - ✅ RIGHT: `mutate(date_col = ymd(col))`

2. **Date Math:**
   - Calculate differences using simple subtraction: `date2 - date1`.
   - **ALWAYS** convert the result to numeric immediately: `as.numeric(date2 - date1)`.
   - ❌ WRONG: `interval(days = 0)`
   - ✅ RIGHT: `filter(delay >= 0)`

3. **Pipeline Context:**
   - If the spec implies columns exist from a previous step (e.g. `date_death`), assume they are **already Date objects**. Do not parse them again.
   - Do not use `read.csv`.

### SPECIFICATION:
{spec_content}

### OUTPUT:
Only the R code.
"""

def run_architect(manifest_path="migration_manifest.json"):
    # (This function remains exactly the same as your current version)
    # Just ensure it uses the updated ARCHITECT_PROMPT above.
    if not os.path.exists(manifest_path):
        # Fallback for the dummy repo if running from migration root
        manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    for entry in manifest:
        if entry['role'] == 'controller':
            continue

        print(f"🏛️  Architecting {entry['r_function_name']}...")
        
        # Load the Spec
        spec_path = entry['spec_file']
        if not os.path.exists(spec_path):
            print(f"   ⚠️ Spec not found: {spec_path}. Run Analyst first.")
            continue
            
        with open(spec_path, 'r') as f:
            spec_content = f.read()

        # INJECT THE NAME FROM MANIFEST
        prompt = ARCHITECT_PROMPT.format(
            target_name=entry['r_function_name'],
            spec_content=spec_content
        )
        
        r_code = get_ollama_response(prompt)
        
        # Cleanup
        if "```r" in r_code: r_code = r_code.split("```r")[1].split("```")[0]
        elif "```" in r_code: r_code = r_code.split("```")[1].split("```")[0]

        # Save to the specific path defined in Manifest
        os.makedirs(os.path.dirname(entry['r_file']), exist_ok=True)
        with open(entry['r_file'], 'w') as f:
            f.write(r_code.strip())
            
        print(f"   ✅ Saved to {entry['r_file']}")

if __name__ == "__main__":
    run_architect()