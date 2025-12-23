import unittest
import sys
import os

def run_tests():
    print("🛡️  RUNNING MIGRATION FRAMEWORK TESTS")
    print("=======================================")
    
    # Auto-discover tests in the 'tests' folder
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    if not os.path.exists(start_dir):
        print("❌ 'tests' directory not found. Creating it...")
        os.makedirs(start_dir)
        
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ FRAMEWORK HEALTHY. Safe to run pipeline.")
        sys.exit(0)
    else:
        print("\n🛑 FRAMEWORK BROKEN. Fix Python errors before running pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()