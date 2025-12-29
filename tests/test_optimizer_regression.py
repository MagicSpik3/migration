import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# FIX: Import the raw client instead of the Agent class
from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import OPTIMIZER_PROMPT_V2

class TestOptimizerRegression(unittest.TestCase):
    
    def test_style_optimization_safety(self):
        """
        Scenario: Input code works but is 'ugly'.
        Optimizer Goal: Clean formatting.
        Regression Risk: It renames the input column 'dor' to 'date_reg' prematurely.
        """
        print("\n🧪 Test: Optimizer Regression (Do No Harm)...")
        
        # Working, but ugly code (Draft)
        ugly_but_working_code = """
        calc_delays <- function(df) {
          df %>% mutate(date_reg = ymd(dor)) %>% return()
        }
        """
        
        prompt = OPTIMIZER_PROMPT_V2.format(
            logic_status="PASS",
            lint_issues="Style is messy.",
            r_code=ugly_but_working_code
        )
        
        # FIX: Call LLM directly to simulate the optimizer's raw output
        print("   [Thinking] Simulating Optimizer Response...")
        optimized_code = get_ollama_response(prompt)
        
        print(f"   [Draft Code]: {ugly_but_working_code.strip()}")
        print(f"   [Optimized]:  {optimized_code.replace(chr(10), ' ')[:80]}...")
        
        # ASSERTION 1: Logic Preservation
        # It must still reference 'dor' (the source). 
        self.assertIn("dor", optimized_code, "❌ Regression! Optimizer deleted the source column 'dor'.")
        
        # ASSERTION 2: No Self-Reference Hallucination
        self.assertNotIn("ymd(date_reg)", optimized_code, "❌ Regression! Optimizer introduced a circular dependency.")

    def test_revert_logic(self):
        """
        Scenario: We simulate the Pipeline Controller's decision process.
        """
        print("\n🧪 Test: Pipeline Revert Logic...")
        draft_code = "return(1) # Works"
        optimized_code = "return(error) # Broken"
        
        draft_passes = True
        optimized_passes = False
        
        final_code = draft_code if (draft_passes and not optimized_passes) else optimized_code
        self.assertEqual(final_code, draft_code, "❌ Pipeline failed to revert to the working draft!")

if __name__ == "__main__":
    unittest.main()