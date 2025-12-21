import os
from src.utils.ollama_client import get_ollama_response


REFACTORING_PROMPT = """
You are a Senior R Developer refactoring legacy code.
Your goal is to delete "Translation Artifacts" and replace them with idiomatic Tidyverse functions.

### PATTERN MATCHING RULES (SEARCH & DESTROY):

1. **The "SPSS Date Math" Pattern:**
   * IF you see: `as.numeric(substr(var, 1, 4)) * 10000 + ...`
   * OR: `trunc(num / 10000)`
   * REPLACE WITH: `lubridate::ymd(var)` or `as.Date(var, format="%Y%m%d")`
   * REASON: The input is just a "YYYYMMDD" string. Parse it directly.

2. **The "Flip" Pattern:**
   * IF you see: `date_death - date_reg` (Death minus Registration)
   * AND the business logic is "Registration Delay"
   * WARNING: This calculates a negative number if Reg is before Death.
   * ACTION: Ensure the logic matches the intent. If it creates a variable named `delay`, it usually implies `Registration - Death`.

3. **General Cleanups:**
   * Remove `rowwise()` if used.
   * Use pipes `%>%`.

### INPUT R CODE:
{r_code}

### OUTPUT:
Provide ONLY the refactored R code.
"""


def refactor_file(file_path):
    with open(file_path, 'r') as f:
        original_code = f.read()

    print(f"Refactoring {os.path.basename(file_path)}...")
    
    prompt = REFACTORING_PROMPT.format(r_code=original_code)
    response = get_ollama_response(prompt)
    
    # Cleanup Markdown
    if "```r" in response:
        cleaned_code = response.split("```r")[1].split("```")[0]
    elif "```" in response:
        cleaned_code = response.split("```")[1].split("```")[0]
    else:
        cleaned_code = response

    return cleaned_code.strip()

if __name__ == "__main__":
    # Input: The folder where your "Bad R" (Literal Translation) lives
    INPUT_DIR = os.path.expanduser("~/git/dummy_spss_repo/r_migrated")
    # Output: A new folder for the "Good R"
    OUTPUT_DIR = os.path.expanduser("~/git/dummy_spss_repo/r_refactored")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith(".R"):
                input_path = os.path.join(root, file)
                
                # Refactor
                new_code = refactor_file(input_path)
                
                # Save
                output_path = os.path.join(OUTPUT_DIR, file)
                with open(output_path, 'w') as f:
                    f.write(new_code)
                
                print(f"✅ Saved clean code to {output_path}")