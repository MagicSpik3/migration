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

def debug_one_shot():
    target_func = "calc_delays"
    qa = QAEngineer()
    
    # 1. Load Manifest Entry
    with open(qa.manifest_path, 'r') as f:
        manifest = json.load(f)
    entry = next((e for e in manifest if e['r_function_name'] == target_func), None)
    
    if not entry:
        print(f"❌ Function {target_func} not found in manifest.")
        return

    test_path = os.path.join(qa.test_dir, f"test_{target_func}.R")

    # 2. Generate Test (One time only)
    print(f"🚀 Generating Test for {target_func}...")
    qa.generate_tests(entry)
    
    if not os.path.exists(test_path):
        print("❌ Failed to generate test file.")
        return

    # 3. Print the Code
    with open(test_path, 'r') as f:
        print_box("GENERATED R CODE", f.read())

    # 4. Run the Test
    print(f"🏃 Running {test_path}...")
    cmd = ["Rscript", "-e", f"library(testthat); test_file('{test_path}')"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 5. Report Results
    if "Failure" not in result.stdout and "Error" not in result.stdout:
        print_box("✅ SUCCESS", result.stdout)
    else:
        print_box("❌ FAILURE", result.stdout)

if __name__ == "__main__":
    debug_one_shot()