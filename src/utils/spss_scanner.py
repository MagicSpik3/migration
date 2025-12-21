import os
import re
from collections import Counter

class SPSSCommandScanner:
    def __init__(self):
        # Master List of Valid SPSS Commands (The "Allow List")
        self.valid_commands = {
            'ADD FILES', 'AGGREGATE', 'ALTER TYPE', 'AUTORECODE', 'CASESTOVARS', 
            'COMPUTE', 'CORRELATIONS', 'CROSSTABS', 'DATA LIST', 'DATASET ACTIVATE', 
            'DATASET CLOSE', 'DATASET DECLARE', 'DATASET NAME', 'DELETE VARIABLES', 
            'DESCRIPTIVES', 'DO IF', 'DO REPEAT', 'ELSE', 'END CASE', 'END FILE', 
            'END IF', 'END LOOP', 'END REPEAT', 'ERASE', 'EXAMINE', 'EXECUTE', 
            'EXPORT', 'FILTER', 'FLIP', 'FORMATS', 'FREQUENCIES', 'GET', 'GET DATA', 
            'GRAPH', 'IF', 'IMPORT', 'INPUT PROGRAM', 'INSERT', 'LIST', 'LOOP', 
            'MATCH FILES', 'MEANS', 'MISSING VALUES', 'MODIFY VARS', 'NPAR TESTS', 
            'NUMERIC', 'OMS', 'ONEWAY', 'OUTPUT', 'PERMISSIONS', 'PRESERVE', 'PRINT', 
            'RANK', 'RECODE', 'REGRESSION', 'RELIABILITY', 'RENAME VARIABLES', 
            'RESTORE', 'SAVE', 'SAVE TRANSLATE', 'SELECT IF', 'SET', 'SHOW', 
            'SORT CASES', 'SPLIT FILE', 'STRING', 'SUBTITLE', 'SUMMARIZE', 
            'TEMPORARY', 'TITLE', 'T-TEST', 'UNIANOVA', 'UPDATE', 'USE', 
            'VALUE LABELS', 'VARIABLE LABELS', 'VARSTOCASES', 'VECTOR', 'WEIGHT', 
            'WRITE'
        }
        
        # Regex to capture the first word of a line
        self.pattern = re.compile(r'^\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)', re.MULTILINE)

    def scan_directory(self, dir_path):
        command_counts = Counter()
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith('.sps'):
                    full_path = os.path.join(root, file)
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Find matches
                    matches = self.pattern.findall(content)
                    
                    for m in matches:
                        # Normalize: Uppercase and take first word (mostly)
                        # We handle multi-word commands like "DATA LIST" by checking prefixes
                        candidate = m.upper().strip()
                        first_word = candidate.split()[0]
                        
                        # Check exact match or first word match
                        if candidate in self.valid_commands:
                            command_counts[candidate] += 1
                        elif first_word in self.valid_commands:
                            command_counts[first_word] += 1
                        elif candidate.startswith("GET DATA"): # Special handling
                             command_counts["GET DATA"] += 1
        
        return command_counts

if __name__ == "__main__":
    repo_path = os.path.expanduser("~/git/dummy_spss_repo")
    if os.path.exists(repo_path):
        scanner = SPSSCommandScanner()
        counts = scanner.scan_directory(repo_path)
        print(f"--- Found {len(counts)} Valid SPSS Commands ---")
        for cmd, count in counts.most_common():
            print(f"{cmd:<20} | {count:<5}")