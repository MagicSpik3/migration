import os
import json

class PipelineController:
    def __init__(self, manifest_path="migration_manifest.json"):
        self.manifest_path = os.path.abspath(manifest_path)
        if not os.path.exists(self.manifest_path):
            self.manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
            
        with open(self.manifest_path, 'r') as f:
            self.manifest = json.load(f)

        # Derive repo root from the first file path in manifest
        first_r = self.manifest[0]['r_file']
        if not os.path.isabs(first_r):
            first_r = os.path.abspath(os.path.join(os.path.dirname(self.manifest_path), first_r))
        self.repo_root = os.path.dirname(os.path.dirname(first_r))
        self.output_path = os.path.join(self.repo_root, "main.R")

    def generate_main(self):
        print(f"--- Building main.R at {self.output_path} ---")
        
        lines = []
        lines.append("# --- DETERMINISTIC PIPELINE CONTROLLER ---")
        lines.append("# This script is auto-generated. Do not edit manually.")
        lines.append("")
        
        # 1. Boilerplate: Set Working Directory
        lines.append("tryCatch({")
        lines.append("  setwd(dirname(rstudioapi::getActiveDocumentContext()$path))")
        lines.append("}, error = function(e) {")
        lines.append("  args <- commandArgs(trailingOnly = FALSE)")
        lines.append("  file_arg <- grep('--file=', args, value = TRUE)")
        lines.append("  if (length(file_arg) > 0) {")
        lines.append("    setwd(dirname(sub('--file=', '', file_arg)))")
        lines.append("  }")
        lines.append("})")
        lines.append("")
        
        # 2. Libraries
        lines.append("suppressPackageStartupMessages(library(dplyr))")
        lines.append("suppressPackageStartupMessages(library(lubridate))")
        lines.append("")
        
        # 3. Source Logic Functions
        lines.append("# --- 1. Load Generated Functions ---")
        for entry in self.manifest:
            if entry['role'] == 'logic':
                # Use absolute path for safety
                r_path = entry['r_file']
                # If relative, make it absolute based on repo root
                if not os.path.isabs(r_path):
                    r_path = os.path.join(self.repo_root, r_path)
                # Escape backslashes for Windows, though we are on Linux
                lines.append(f'source("{r_path}")')
        lines.append("")
        
        # 4. Load Data
        lines.append("# --- 2. Load Data ---")
        lines.append('input_path <- "input_data.csv"')
        lines.append('if(!file.exists(input_path)) stop(paste("Missing:", input_path))')
        lines.append('df <- read.csv(input_path, colClasses = "character")')
        lines.append("")
        
        # 5. Execute Chain
        lines.append("# --- 3. Execute Logic Chain ---")
        for entry in self.manifest:
            if entry['role'] == 'logic':
                func = entry['r_function_name']
                lines.append(f"print('Running {func}...')")
                lines.append(f"df <- {func}(df)")
        lines.append("")
        
        # 6. Export
        lines.append("# --- 4. Export ---")
        lines.append('write.csv(df, "final_output.csv", row.names = FALSE)')
        lines.append('print("✅ Pipeline Complete. Saved to final_output.csv")')
        
        with open(self.output_path, 'w') as f:
            f.write("\n".join(lines))
            
        print(f"✅ Generated Controller: {self.output_path}")

if __name__ == "__main__":
    controller = PipelineController()
    controller.generate_main()