import os
import json
import re
from src.utils.dependency_resolver import DependencyResolver

class ManifestManager:
    def __init__(self, spss_dir, manifest_path="migration_manifest.json"):
        self.spss_dir = os.path.abspath(spss_dir)
        self.manifest_path = os.path.abspath(manifest_path)
        self.repo_root = os.path.dirname(self.spss_dir)
        self.specs_dir = os.path.join(self.repo_root, "specs")
        self.r_dir = os.path.join(self.repo_root, "r_from_spec")

    def sanitize_function_name(self, filename):
        """
        Converts '01_calc_delays.sps' -> 'calc_delays'
        """
        base = os.path.splitext(filename)[0].lower()
        # Remove leading numbers/underscores (e.g., "01_")
        clean_name = re.sub(r'^\d+[_]*', '', base)
        return clean_name.replace(" ", "_")

    def determine_role(self, file_path):
        """
        Analyzes file content to determine if it's a Controller or Logic.
        Rule: If it contains INSERT or INCLUDE commands, it's a Controller.
        """
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            # Regex to look for INSERT or INCLUDE command (case insensitive)
            # Matches: INSERT FILE=... or INCLUDE FILE=...
            is_controller = re.search(r'^\s*(INSERT|INCLUDE)\s+FILE=', content, re.MULTILINE | re.IGNORECASE)
            
            if is_controller:
                return "controller"
            else:
                return "logic"
                
        except Exception as e:
            print(f"⚠️ Could not read {file_path}: {e}")
            return "logic" # Default assumption

    def generate_manifest(self):
        print("--- Initializing Smart Manifest ---")
        
        # 1. Resolve Dependencies (Still needed for execution order)
        resolver = DependencyResolver(self.spss_dir)
        resolver.scan()
        ordered_files = resolver.get_execution_order()
        
        # Save architecture doc
        resolver.generate_architecture_doc(os.path.join(self.repo_root, "architecture.md"))
        
        manifest = []
        
        for filename in ordered_files:
            full_path = resolver.file_map[filename]
            
            # 1. Sanitize Name
            r_func_name = self.sanitize_function_name(filename)
            
            # 2. Determine Role by Content (The Fix)
            role = self.determine_role(full_path)
            
            entry = {
                "legacy_file": full_path,
                "legacy_name": filename,
                "r_function_name": r_func_name,
                "role": role,
                "spec_file": os.path.join(self.specs_dir, f"{r_func_name}.md"),
                "r_file": os.path.join(self.r_dir, f"{r_func_name}.R"),
                "status": "pending"
            }
            manifest.append(entry)
            print(f"   Mapped {filename} -> {r_func_name} ({role})")
        
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)
        
        print(f"✅ Manifest generated. Check {self.manifest_path}")

if __name__ == "__main__":
    # Ensure this points to where your .sps files actually are
    ROOT = os.path.expanduser("~/git/dummy_spss_repo/syntax")
    
    manager = ManifestManager(ROOT)
    manager.generate_manifest()