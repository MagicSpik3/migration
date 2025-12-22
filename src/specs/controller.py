import json
import os

class PipelineController:
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = os.path.abspath(manifest_path)





# ... inside generate_main loop ...
        


        # ... (Data Loading stays the same) ...









    def generate_main(self):
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        # Determine the Target Repo Root (One level up from the 'r_from_spec' folder)
        # We grab the first entry to find the path
        first_r_file = manifest[0]['r_file']
        repo_root = os.path.dirname(os.path.dirname(first_r_file))
        output_file = os.path.join(repo_root, "main.R")

        print(f"--- Building main.R at {output_file} ---")
        
        lines = []
        lines.append("# --- DETERMINISTIC PIPELINE CONTROLLER ---")
        
        # Robust Path Setting (Works in RStudio, VSCode, and CLI)
        lines.append("tryCatch({")
        lines.append("  setwd(dirname(rstudioapi::getActiveDocumentContext()$path))")
        lines.append("}, error = function(e) {")
        lines.append("  # If not in RStudio, try CLI arg or fallback")
        lines.append("  args <- commandArgs(trailingOnly = FALSE)")
        lines.append("  file_arg <- grep('--file=', args, value = TRUE)")
        lines.append("  if (length(file_arg) > 0) {")
        lines.append("    setwd(dirname(sub('--file=', '', file_arg)))")
        lines.append("  }")
        lines.append("})")
        
        lines.append("library(dplyr)")
        lines.append("library(lubridate)")
        lines.append("")
        

        # 1. Load Functions (Only Logic)
        lines.append("# 1. Load Generated Functions")
        for entry in manifest:
            if entry['role'] == 'controller':
                continue # Skip loading the legacy controller script
                
            r_path = entry['r_file'].replace("\\", "/")
            lines.append(f'source("{r_path}")')



        lines.append("")
        lines.append("# 2. Load Data")
        # We assume input_data.csv is in the same folder as main.R
        lines.append('input_path <- "input_data.csv"')
        lines.append('if(!file.exists(input_path)) stop(paste("Missing:", input_path))')
        lines.append('df <- read.csv(input_path, colClasses = "character")')
        lines.append("")


        # 3. Execution Loop
        lines.append("# 3. Execute Logic Chain")
        for entry in manifest:
            if entry['role'] == 'controller':
                continue # Do not try to run the controller as a function!
                
            func_name = entry['r_function_name']
            lines.append(f"print('Running {func_name}...')")
            lines.append(f"df <- {func_name}(df)")
            lines.append("")


        lines.append("# 4. Export")
        lines.append('write.csv(df, "final_output.csv", row.names = FALSE)')
        lines.append('print("✅ Pipeline Complete. Saved to final_output.csv")')

        with open(output_file, 'w') as f:
            f.write("\n".join(lines))
        
        print(f"✅ Generated Controller: {output_file}")

if __name__ == "__main__":
    controller = PipelineController()
    controller.generate_main()