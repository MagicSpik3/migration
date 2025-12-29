import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.specs.qa_engineer import QAEngineer

def debug_qa_generation():
    print("🔬 DEBUGGING QA TEST GENERATION")
    print("=================================")
    
    qa = QAEngineer()
    
    # 1. Load Manifest
    manifest_path = os.path.expanduser("~/git/dummy_spss_repo/migration_manifest.json")
    if not os.path.exists(manifest_path):
        manifest_path = "migration_manifest.json"
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    target_func = "calc_delays"
    entry = next((e for e in manifest if e['r_function_name'] == target_func), None)
    
    if not entry:
        print(f"❌ Could not find {target_func} in manifest.")
        return

    print(f"\n[1] Generating Test Suite for: {target_func}...")
    
    # 2. Run Generation (Fix: use correct method name)
    # Note: This likely returns True/False, not the path.
    qa.generate_tests(entry)
    
    # 3. Find the file manually
    repo_root = os.path.dirname(manifest_path)
    test_file_path = os.path.join(repo_root, "tests", f"test_{target_func}.R")
    
    if os.path.exists(test_file_path):
        print(f"   ✅ Test file found at: {test_file_path}")
        print("\n" + "="*60)
        print("📜 GENERATED R TEST CODE")
        print("="*60)
        
        with open(test_file_path, 'r') as f:
            print(f.read())
            
        print("="*60)
    else:
        print(f"❌ Test file not found at expected location: {test_file_path}")

if __name__ == "__main__":
    debug_qa_generation()