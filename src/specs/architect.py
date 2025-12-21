import os
from src.utils.ollama_client import get_ollama_response

ARCHITECT_PROMPT = """
You are a Senior R Package Developer.
Your task is to implement the following **Technical Specification** as a robust, exported R function.

### SPECIFICATION:
{spec_content}

### ARCHITECTURAL STANDARDS:
1. **Structure:** - Output a single function named `{func_name}`.
   - Use `roxygen2` documentation (Title, Description, @param, @return, @export).
   - Input: A dataframe. Output: A dataframe.
2. **Logic Implementation:**
   - Use `dplyr` and `lubridate`.
   - **Dates:** Use `ymd()` or `as.Date()`. Do NOT use `substr` math.
   - **Math:** Ensure `Registration - Death` is calculated correctly (should be positive).
3. **Validation vs. Filtering:**
   - If the spec says "Error on negative values" or "Validation Rule", use `stop()` or `assert`.
   - If the spec says "Exclude" or "Filter", use `filter()`.
   - *Check the intent carefully.*

### OUTPUT:
Provide ONLY the R code for the function. Do not include library calls or dummy data setup.
"""

def build_from_spec(spec_path, output_dir):
    # Derive function name from filename (e.g. calc_delays.md -> calc_delays)
    func_name = os.path.basename(spec_path).replace('.md', '')
    filename = func_name + '.R'
    
    print(f"Architecting function '{func_name}'...")
    
    with open(spec_path, 'r') as f:
        spec = f.read()
        
    prompt = ARCHITECT_PROMPT.format(spec_content=spec, func_name=func_name)
    r_code = get_ollama_response(prompt)
    
    # Cleanup Markdown
    if "```r" in r_code:
        r_code = r_code.split("```r")[1].split("```")[0]
    elif "```" in r_code:
        r_code = r_code.split("```")[1].split("```")[0]
        
    out_path = os.path.join(output_dir, filename)
    with open(out_path, 'w') as f:
        f.write(r_code.strip())
    print(f"✅ R Function saved to {out_path}")

if __name__ == "__main__":
    SPEC_DIR = os.path.expanduser("~/git/dummy_spss_repo/specs")
    OUTPUT_DIR = os.path.expanduser("~/git/dummy_spss_repo/r_from_spec")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for root, dirs, files in os.walk(SPEC_DIR):
        for file in files:
            if file.endswith(".md"):
                build_from_spec(os.path.join(root, file), OUTPUT_DIR)