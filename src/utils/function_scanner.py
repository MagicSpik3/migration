import re
import os

class RFunctionScanner:
    def __init__(self):
        # Regex to capture:
        # 1. package::function (e.g., dplyr::mutate)
        # 2. function( (e.g., mutate() )
        self.pattern = re.compile(r'([\w\.]+::[\w\.]+|[\w\.]+(?=\())')
        
        # Ignore common base syntax constructs that aren't really "functions" to map
        self.ignore_list = {
            'c', 'list', 'function', 'if', 'else', 'return', 'library', 'stop', 
            'unique', 'names', 'min', 'max', 'sum', 'round', 'paste', 'paste0'
        }

    def scan_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Remove comments to avoid false positives
        content = re.sub(r'#.*', '', content)
        
        matches = self.pattern.findall(content)
        unique_funcs = sorted(list(set(matches)))
        
        # Filter out ignored
        filtered = [f for f in unique_funcs if f not in self.ignore_list and "::" not in f]
        namespaced = [f for f in unique_funcs if "::" in f]
        
        return filtered + namespaced

if __name__ == "__main__":
    # Test on your file
    scanner = RFunctionScanner()
    # Update path to match your actual file
    r_file = "/home/jonny/git/weekly_deaths_rap/weekly.deaths/R/registration_delays.R"
    
    if os.path.exists(r_file):
        funcs = scanner.scan_file(r_file)
        print(f"Found {len(funcs)} unique functions:")
        for f in funcs:
            print(f" - {f}")
    else:
        print("File not found. Update the path in the script.")