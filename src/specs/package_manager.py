import os
import re
import datetime

class PackageManager:
    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.r_dir = os.path.join(repo_root, "r_from_spec")
        self.desc_path = os.path.join(repo_root, "DESCRIPTION")

    def scan_dependencies(self):
        """Scans all .R files for 'package::' patterns."""
        dependencies = set()
        
        # Core defaults
        dependencies.add("dplyr") 
        dependencies.add("magrittr") # for %>%
        dependencies.add("readr")    # for write_csv
        
        if not os.path.exists(self.r_dir):
            return list(dependencies)

        # Regex to find pkg::func (excludes comments and :::)
        pattern = re.compile(r'(?<!#)\b([a-zA-Z0-9\.]+)::')
        
        for filename in os.listdir(self.r_dir):
            if not filename.endswith(".R"): continue
            
            with open(os.path.join(self.r_dir, filename), 'r') as f:
                content = f.read()
                matches = pattern.findall(content)
                for pkg in matches:
                    if pkg not in ["base", "stats", "utils", "graphics", "methods"]:
                        dependencies.add(pkg)
                        
        return sorted(list(dependencies))

    def generate_description(self):
        print("📦 Building DESCRIPTION file...")
        deps = self.scan_dependencies()
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        
        content = f"""Package: migrationRepo
Title: Auto-Migrated SPSS Logic
Version: 0.1.0
Date: {date_str}
Description: Logic migrated from legacy SPSS syntax.
Imports:
"""
        content += "    " + ",\n    ".join(deps) + "\n"
        content += "Encoding: UTF-8\nRoxygenNote: 7.2.3\n"
        
        with open(self.desc_path, 'w') as f:
            f.write(content)
        
        print(f"   ✅ Saved to {self.desc_path}")
        print(f"   🔗 Detected Dependencies: {', '.join(deps)}")

if __name__ == "__main__":
    target = os.path.expanduser("~/git/dummy_spss_repo")
    pm = PackageManager(target)
    pm.generate_description()