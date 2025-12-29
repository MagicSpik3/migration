
import sys
import os
import json
import subprocess

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.specs.qa_engineer import QAEngineer

def print_box(title, content):
    print(f"\n╔{'═'*(len(title)+2)}╗")
    print(f"║ {title} ║")
    print(f"╚{'═'*(len(title)+2)}╝")
    print(content)
    print("-" * 60)

def debug_qa_iterator(target_func="calc_delays"):
    qa = QAEngineer()
    
    # 1. Find Entry
    with open(qa.manifest_path, 'r') as f:
        manifest = json.load(f)
    entry = next((e for e in manifest if e['r_function_name'] == target_func), None)
    
    if not entry:
        print(f"❌ Function {target_func} not found in manifest.")
        return

    test_path = os.path.join(qa.test_dir, f"test_{target_func}.R")

    # --- PHASE 1: GENERATION ---
    print(f"\n🚀 PHASE 1: Generating Initial Test for {target_func}...")
    qa.generate_tests(entry)
    
    if os.path.exists(test_path):
        with open(test_path, 'r') as f:
            print_box("GENERATED TEST CODE", f.read())
    else:
        print("❌ Failed to generate test file.")
        return

    # --- PHASE 2: ITERATIVE TESTING ---
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\n🏃 PHASE 2 (Attempt {attempt}): Running Test...")
        
        cmd = ["Rscript", "-e", f"library(testthat); test_file('{test_path}')"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check Success
        if "Failure" not in result.stdout and "Error" not in result.stdout:
            print_box(f"✅ SUCCESS (Attempt {attempt})", result.stdout)
            return

        # It Failed
        print_box(f"❌ FAILURE (Attempt {attempt})", result.stdout)
        
        # Extract Error for Analysis
        error_lines = [line for line in result.stdout.split('\n') 
                      if any(x in line for x in ["Failure:", "Error:", "Difference:", "Expected"])]
        error_summary = "\n".join(error_lines)
        print(f"🔍 ANALYZED ERROR:\n{error_summary}")

        if attempt < max_attempts:
            print(f"\n🩹 Attempting to HEAL test logic based on error...")
            qa.fix_broken_test(entry, result.stdout[-2000:])
            
            # Show the Diff (Simple approach: just print new code)
            with open(test_path, 'r') as f:
                print_box(f"HEALED CODE (Ready for Attempt {attempt+1})", f.read())
        else:
            print("\n💀 Exhausted all attempts.")

if __name__ == "__main__":
    # Default to calc_delays, or pass arg
    func = sys.argv[1] if len(sys.argv) > 1 else "calc_delays"
    debug_qa_iterator(func)
