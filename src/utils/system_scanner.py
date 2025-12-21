import os
import re

class SystemScanner:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.dependencies = []
        self.external_inputs = []
        self.macros = []

    def scan(self):
        print(f"--- Scanning System Logic in {self.repo_path} ---")
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.lower().endswith('.sps'):
                    self.analyze_file(os.path.join(root, file))
        
        self.report()

    def analyze_file(self, path):
        filename = os.path.basename(path)
        with open(path, 'r', errors='ignore') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line = line.strip().upper()
            
            # 1. Detect External Drivers (Excel/Text inputs)
            if "GET DATA" in line or "GET TRANSLATE" in line:
                if "TYPE=XLS" in line or "TYPE=ODBC" in line or ".XLS" in line:
                    self.external_inputs.append(f"{filename}:{i+1} reads External Data (Likely Driver)")

            # 2. Detect Control Flow (Chaining)
            if line.startswith("INSERT") or line.startswith("INCLUDE"):
                target = re.search(r"FILE=['\"]?([^'\"]+)['\"]?", line)
                if target:
                    self.dependencies.append(f"{filename} -> {target.group(1)}")

            # 3. Detect Macros (The logic engine)
            if line.startswith("DEFINE"):
                macro_name = line.split()[1]
                self.macros.append(f"{filename} defines Macro: {macro_name}")

    def report(self):
        print("\n=== SYSTEM DRIVERS (The 'Excel' Logic) ===")
        for item in self.external_inputs:
            print(f"  [INPUT] {item}")
            
        print("\n=== CONTROL FLOW (Script Chaining) ===")
        for item in self.dependencies:
            print(f"  [LINK]  {item}")
            
        print("\n=== MACRO LOGIC (Hidden Complexity) ===")
        for item in self.macros:
            print(f"  [MACRO] {item}")

if __name__ == "__main__":
    # Point this to your REAL repo if you can, or the dummy one
    scanner = SystemScanner(os.path.expanduser("~/git/dummy_spss_repo"))
    scanner.scan()