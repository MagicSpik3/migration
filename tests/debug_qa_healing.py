import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.specs.qa_engineer import QAEngineer

def debug_healing():
    print("🔬 DEBUGGING QA SELF-HEALING")
    print("============================")
    
    qa = QAEngineer()
    
    # 1. SETUP: Create a "Broken" Test File manually
    # We pretend there is a function called 'dummy_func'
    func_name = "dummy_func"
    test_path = os.path.join(qa.test_dir, f"test_{func_name}.R")
    
    print(f"[Setup] Creating broken test at {test_path}...")
    with open(test_path, 'w') as f:
        f.write("""
library(testthat)
test_that("dummy_func works", {
    expect_equal(1, 2) # <--- THIS WILL FAIL
})
""")

    # 2. ACTION: Simulate a Failure Event
    # We construct a fake manifest entry just for this test
    fake_entry = {
        'r_function_name': func_name, 
        'r_file': 'dummy_path.R' # Won't be read by fix_broken_test directly
    }
    
    fake_error_log = """
    Failure (test_dummy_func.R:3:5): dummy_func works
    1 not equal to 2.
    """
    
    print("[Action] Triggering Self-Healing...")
    try:
        # This is where it crashed before
        success = qa.fix_broken_test(fake_entry, fake_error_log)
        
        if success:
            print("\n✅ Healing Triggered Successfully (No Crash!)")
            print("   The LLM attempted to write a fix.")
            
            # Check if file changed
            with open(test_path, 'r') as f:
                new_content = f.read()
            print(f"\n[New Content Snippet]:\n{new_content[:200]}...")
            
        else:
            print("\n❌ Healing Failed (returned False).")
            
    except AttributeError as e:
        print(f"\n🔥 CRITICAL ERROR: The crash persists!")
        print(f"   {e}")
    except Exception as e:
        print(f"\n⚠️ Unexpected Error: {e}")

    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)

if __name__ == "__main__":
    debug_healing()