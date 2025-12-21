import os
import pandas as pd
from src.utils.ollama_client import get_ollama_response

SYSTEM_PROMPT = """
You are an Expert R Developer migrating legacy SPSS code to the Tidyverse.
Your goal is to produce clean, modern, and reproducible R code.

### ARCHITECTURAL RULES (CRITICAL):
1. **Pipeline over Steps:** Convert sequential SPSS commands into `dplyr` pipelines (`%>%`) where possible.
2. **State Management:** SPSS `SELECT IF` permanently filters the dataset. In R, you MUST overwrite the object: `df <- df %>% filter(...)`.
3. **Variable Types:** SPSS treats everything as generic. In R, explicitly handle types (e.g., `as.Date`, `as.numeric`).

### ROSETTA STONE (USE THIS MAPPING):
{mapping_table}
"""

class SPSSMigrationAgent:
    def __init__(self, rosetta_path="r_rosetta_stone.csv"):
        # Load the Rosetta Stone to guide the LLM
        if os.path.exists(rosetta_path):
            df = pd.read_csv(rosetta_path)
            self.mapping_table = df.to_markdown(index=False)
        else:
            self.mapping_table = "No mapping table found."
            print("[WARNING] Rosetta Stone not found. Relying on LLM knowledge.")

    def migrate_file(self, sps_path, output_dir):
        with open(sps_path, 'r') as f:
            spss_code = f.read()

        filename = os.path.basename(sps_path).replace('.sps', '.R')
        
        prompt = (
            f"{SYSTEM_PROMPT.format(mapping_table=self.mapping_table)}\n\n"
            f"TASK: Convert the following SPSS syntax to an R script.\n"
            f"Assume the input data is loaded into a dataframe called `df`.\n\n"
            f"SPSS CODE:\n{spss_code}\n\n"
            f"OUTPUT:\nProvide ONLY the R code. Do not include markdown ticks."
        )

        print(f"Migrating {filename}...")
        r_code = get_ollama_response(prompt)
        
        # Cleanup Markdown
        if "```r" in r_code:
            r_code = r_code.split("```r")[1].split("```")[0]
        elif "```" in r_code:
            r_code = r_code.split("```")[1].split("```")[0]

        # Save
        out_path = os.path.join(output_dir, filename)
        with open(out_path, 'w') as f:
            f.write(r_code.strip())
        
        print(f"✅ Saved to {out_path}")

if __name__ == "__main__":
    # Config
    REPO_DIR = os.path.expanduser("~/git/dummy_spss_repo/syntax")
    OUTPUT_DIR = os.path.expanduser("~/git/dummy_spss_repo/r_migrated")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    agent = SPSSMigrationAgent()
    
    # Batch Migrate
    for root, dirs, files in os.walk(REPO_DIR):
        for file in files:
            if file.endswith(".sps"):
                agent.migrate_file(os.path.join(root, file), OUTPUT_DIR)