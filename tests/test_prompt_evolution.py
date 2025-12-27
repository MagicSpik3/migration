import unittest
import os
import sys
# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.refining_agent import RefiningAgent
from src.specs.prompts import OPTIMIZER_PROMPT_V1, OPTIMIZER_PROMPT_V2

class TestPromptEvolution(unittest.TestCase):

    def setUp(self):
        # The "Toxic" Code that confuses the LLM
        # It has dates as "YYYYMMDD" strings, which tempts the LLM to use str_sub
        self.toxic_code = """
        calc_delays <- function(df) {
            df %>% 
                mutate(date_reg = lubridate::ymd(dor)) %>% # naive attempt
                filter(!is.na(date_reg))
            return(df)
        }
        """
        self.generated_code = ""
        
    def mock_callback(self, code):
        self.generated_code = code
        return False, "Simulated Run" 

    def test_v1_fail_scenario(self):
        """Verify V1 fails (it often produces invalid arguments or str_sub)."""
        print("\n🧪 Testing V1 (Legacy Prompt)...")
        agent = RefiningAgent(OPTIMIZER_PROMPT_V1, max_retries=1)
        
        # Inject context manually for V1 simulation
        agent.system_prompt = agent.system_prompt.replace("{r_code}", self.toxic_code)
        
        agent.run(self.toxic_code, self.mock_callback)
        print(f"   [V1 Output snippet]: {self.generated_code[:100]}...")

    def test_v2_improvement(self):
        """Verify V2 explicitly fixes the str_sub hallucination."""
        print("\n🧪 Testing V2 (New Prompt)...")
        
        prompt_with_context = OPTIMIZER_PROMPT_V2.format(
            logic_status="FAILING. Runtime Error: All formats failed to parse.",
            lint_issues="None",
            r_code=self.toxic_code
        )
        
        agent = RefiningAgent(prompt_with_context, max_retries=1)
        agent.run(self.toxic_code, self.mock_callback)
        
        print(f"   [V2 Output snippet]: {self.generated_code[:100]}...")

        # 1. CRITICAL ASSERTION: No str_sub
        self.assertNotIn("str_sub", self.generated_code, 
                         "❌ V2 Failed: It still used str_sub despite the ban!")
        
        # 2. SUCCESS ASSERTION: Any valid date parsing
        # Matches 'ymd(dor)' OR 'as.Date(dor'
        has_ymd = "ymd(dor)" in self.generated_code
        has_as_date = "as.Date(dor" in self.generated_code
        
        self.assertTrue(has_ymd or has_as_date, 
                        f"❌ V2 Failed: Did not find valid date parsing. Got: {self.generated_code[:50]}...")

if __name__ == "__main__":
    unittest.main()