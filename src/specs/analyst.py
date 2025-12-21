import os
from src.utils.ollama_client import get_ollama_response


ANALYST_PROMPT = """
You are a Technical Business Analyst migrating a complex Legacy System.
Your goal is to Reverse Engineer **Logic** and **Control Flow** from SPSS code.

### TARGET AUDIENCE:
A Senior R Developer who CANNOT run this original code. Your Spec is the ONLY truth.

### ANALYSIS INSTRUCTIONS:

1. **Identify the "Driver":**
   * Does this script read from Excel/Text to set variables? 
   * Does it use `DEFINE !...` (Macros) to change behavior based on inputs?
   * *Requirement:* If you see Macros, describe them as "Configurable Parameters", not code.

2. **Handle Proprietary Syntax:**
   * If you see commands that look like custom extensions or unknown functions, DO NOT GUESS.
   * Mark them in the spec as: `**[RISK] Unknown Syntax: <command>**`
   * Try to infer intent from comments.

3. **Data Dictionary:**
   * List every variable created.
   * Note the Directionality of time (Start -> End).

4. **Logical Complexity:**
   * If the script relies on a global variable set elsewhere, explicitly state: "Requires Global Parameter X".

### SOURCE CODE:
{spss_code}

### OUTPUT FORMAT:
... (Same Markdown structure) ...
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