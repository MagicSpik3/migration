import os
import re
import json

def parse_r_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    functions = []
    current_func = None
    brace_count = 0
    buffer = []
    
    # Regex to find standard R function definitions: my_func <- function(args) {
    func_pattern = re.compile(r'^\s*([a-zA-Z0-9_.]+)\s*<-\s*function\s*\((.*)\)\s*\{')

    for i, line in enumerate(lines):
        # 1. Detect start of function
        match = func_pattern.match(line)
        if match and current_func is None:
            func_name = match.group(1)
            args_raw = match.group(2)
            args = [a.strip().split('=')[0].strip() for a in args_raw.split(',') if a.strip()]
            
            current_func = {
                "function_name": func_name,
                "variables": args,
                "filepath": filepath,
                "repo_name": os.path.basename(os.path.dirname(filepath)),
                "docstring": "No explicit docstring found", # R docs are usually separate .Rd files or comments above
                "start_line": i
            }
            brace_count = 1  # The regex expects a '{' at the end of the line
            buffer = [line]
            continue

        # 2. Capture function body
        if current_func:
            buffer.append(line)
            brace_count += line.count('{')
            brace_count -= line.count('}')

            # 3. Detect end of function
            if brace_count == 0:
                current_func['code_chunk'] = "".join(buffer)
                functions.append(current_func)
                current_func = None
                buffer = []

    return functions

def crawl_and_parse(root_dir, output_file):
    all_functions = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".R"):
                full_path = os.path.join(root, file)
                print(f"Parsing: {full_path}")
                try:
                    funcs = parse_r_file(full_path)
                    all_functions.extend(funcs)
                except Exception as e:
                    print(f"Error parsing {full_path}: {e}")

    with open(output_file, 'w') as f:
        json.dump(all_functions, f, indent=4)
    print(f"Saved {len(all_functions)} functions to {output_file}")

if __name__ == "__main__":
    # 1. Setup Paths relative to the project root
    # This assumes the script is inside src/crawlers/
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Change this to point to your specific R source folder
    # INPUT_DIR = "/home/jonny/git/weekly_deaths_rap/weekly.deaths/R"
    # Or keep it generic if you want to edit it manually:
    INPUT_DIR = "/home/jonny/git/weekly_deaths_rap/weekly.deaths/R" 
    
    OUTPUT_FILE = os.path.join(BASE_DIR, "data", "intermediate", "r_code_data.json")

    # 2. Ensure the output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # 3. Run
    crawl_and_parse(INPUT_DIR, OUTPUT_FILE)
