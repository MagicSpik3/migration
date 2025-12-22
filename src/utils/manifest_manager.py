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
        Rules:
        1. Lowercase.
        2. Remove extension.
        3. Remove leading numbers and underscores (regex).
        """
        base = os.path.splitext(filename)[0].lower()
        # Regex: Start of string (^), followed by digits (\d+) and optional underscores ([_]*)
        clean_name = re.sub(r'^\d+[_]*', '', base)
        return clean_name.replace(" ", "_")

    def generate_manifest(self):
        print("--- Initializing Smart Manifest ---")
        
        # 1. Resolve Dependencies
        resolver = DependencyResolver(self.spss_dir)
        resolver.scan()
        ordered_files = resolver.get_execution_order()
        
        # Save architecture doc for your review
        resolver.generate_architecture_doc(os.path.join(self.repo_root, "architecture.md"))
        
        manifest = []
        
        for filename in ordered_files:
            full_path = resolver.file_map[filename]
            
            # --- FIX 1: Sanitize Names (No numbers) ---
            r_func_name = self.sanitize_function_name(filename)
            
            # --- FIX 2: Detect Controller Role ---
            # If this file calls other files (out-degree > 0), it is a Controller.
            # In our graph (Target points to Caller), this checks if 'filename' is in any list.
            is_controller = False
            for target, callers in resolver.graph.items():
                if filename in callers: # If this file calls someone else
                    is_controller = True
                    break
            
            # Special case for explicit "Run" naming if graph is empty
            if "run" in filename or "pipeline" in filename:
                is_controller = True

            role = "controller" if is_controller else "logic"
            
            entry = {
                "legacy_file": full_path,
                "legacy_name": filename,
                "r_function_name": r_func_name, # Clean name (calc_delays)
                "role": role,                  # logic vs controller
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
    ROOT = os.path.expanduser("~/git/dummy_spss_repo/syntax")
    manager = ManifestManager(ROOT)
    manager.generate_manifest()