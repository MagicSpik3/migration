import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.optimizer import CodeOptimizer

def debug_summary():
    print("🔬 DEBUGGING SUMMARIZE_DEATHS OPTIMIZATION")
    print("==========================================")
    
    optimizer = CodeOptimizer(project_root=os.path.expanduser("~/git/dummy_spss_repo"))
    
    # Run optimization for summarize_deaths only
    with open(optimizer.manifest_path, 'r') as f:
        manifest = json.load(f)
    
    target_entry = next((e for e in manifest if e['r_function_name'] == 'summarize_deaths'), None)
    
    if target_entry:
        print("\n[TARGET] Optimizing summarize_deaths...")
        optimizer.optimize_file(target_entry, force=True)
    else:
        print("❌ Could not find summarize_deaths in manifest.")

if __name__ == "__main__":
    debug_summary()