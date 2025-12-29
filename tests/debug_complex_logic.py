import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.optimizer import CodeOptimizer

def debug_complex_logic():
    print("🔬 DEBUGGING COMPLEX_LOGIC OPTIMIZATION")
    print("=======================================")
    
    optimizer = CodeOptimizer(project_root=os.path.expanduser("~/git/dummy_spss_repo"))
    
    with open(optimizer.manifest_path, 'r') as f:
        manifest = json.load(f)
        
    # 1. SETUP: Must run dependencies first!
    print("\n[SETUP] Running dependencies to populate pipeline state...")
    calc_delays_entry = next((e for e in manifest if e['r_function_name'] == 'calc_delays'), None)
    
    if calc_delays_entry:
        print("   Running calc_delays (to create 'delay_days')...")
        optimizer.optimize_file(calc_delays_entry, force=False)
    else:
        print("   ⚠️ WARNING: calc_delays not found. complex_logic will likely fail.")

    # 2. TARGET: Now run complex_logic
    print("\n[TARGET] Optimizing complex_logic...")
    target_entry = next((e for e in manifest if e['r_function_name'] == 'complex_logic'), None)
    
    if target_entry:
        optimizer.optimize_file(target_entry, force=True)
        
        trace_path = os.path.join(optimizer.debug_dir, "FAILED_complex_logic.txt")
        if os.path.exists(trace_path):
            print("\n" + "="*60)
            print("🛑 FAILURE ANALYSIS (TRACE LOG)")
            with open(trace_path, 'r') as f:
                print(f.read())
        else:
            print("\n✅ No trace found (Success!).")

if __name__ == "__main__":
    debug_complex_logic()