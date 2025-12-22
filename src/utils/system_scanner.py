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
   
            # 4. Detect Time Series / Lag Logic
            if "LAG(" in line or "LEAD(" in line:
                risk = "High" if "SORT" not in last_command else "Low"
                self.time_logic.append(f"{filename}:{i+1} uses LAG/LEAD (Risk: {risk})")
                
            if line.startswith("CREATE"):
                # CREATE is used in SPSS to make moving averages / lags
                self.time_logic.append(f"{filename}:{i+1} uses CREATE (Explicit Time Series gen)")
                
            if line.startswith("TSMODEL") or line.startswith("EXSMOOTH"):
                self.time_logic.append(f"{filename}:{i+1} uses FORECASTING MODELS")

            if line.startswith("SORT CASES"):
                last_command = "SORT"
            elif len(line) > 0 and not line.startswith("*"):
                last_command = line


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

    def generate_mermaid(self, output_path):
            print(f"Generating System Map: {output_path}")
            lines = ["graph TD;"]
            
            # Style definition
            lines.append("    classDef script fill:#f9f,stroke:#333,stroke-width:2px;")
            lines.append("    classDef data fill:#bbf,stroke:#333,stroke-width:2px;")
            
            for item in self.dependencies:
                # item format: "parent.sps -> child.sps"
                parent, child = item.split(" -> ")
                clean_p = parent.replace(".", "_")
                clean_c = child.replace(".", "_")
                lines.append(f"    {clean_p}({parent}) --> {clean_c}({child});")
                lines.append(f"    class {clean_p},{clean_c} script;")

            for item in self.external_inputs:
                # item format: "script.sps:5 reads External Data"
                script = item.split(":")[0]
                clean_s = script.replace(".", "_")
                lines.append(f"    InputData[(External Excel)] --> {clean_s};")
                lines.append(f"    class InputData data;")

            with open(output_path, 'w') as f:
                f.write("```mermaid\n")
                f.write("\n".join(lines))
                f.write("\n```")

if __name__ == "__main__":
    # Point this to your REAL repo if you can, or the dummy one
    scanner = SystemScanner(os.path.expanduser("~/git/dummy_spss_repo"))
    scanner.scan()