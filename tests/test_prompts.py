import unittest
from src.utils.validators import SPSSEvaluator
from src.utils.ollama_client import get_ollama_response # Import from your existing script

# --- The Prompt You Want to Test ---
CANDIDATE_PROMPT_TEMPLATE = """
You are an expert SPSS Syntax writer.
Convert this R list into SPSS VALUE LABELS.

Rules:

1. Format: VALUE LABELS varname value "label".
2. Do not use macros or !IF blocks.
3. End commands with a period.

R CODE:
{r_code}

Output ONLY the SPSS syntax.
"""

# --- The Data You Use for Testing ---
TEST_R_CODE = """
list(
  sex = c("Male", "Female"),
  region = c("North", "South")
)
"""
EXPECTED_VARS = ["sex", "region"]


class TestSPSSPromptQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("--- Generating LLM Response for Testing ---")
        prompt = CANDIDATE_PROMPT_TEMPLATE.format(r_code=TEST_R_CODE)
        
        # Call the API
        cls.llm_output = get_ollama_response(prompt)
        
        # --- SAFETY CHECK (Prevents TypeError crash) ---
        if cls.llm_output is None:
            # If the API fails, we skip the tests instead of letting them crash
            raise unittest.SkipTest("CRITICAL: Ollama connection failed. Skipping verification tests.")
            
        print(f"OUTPUT:\n{cls.llm_output}\n---------------------------------------")
    
    @classmethod
    def setUpClass(cls):
        """Run the LLM once before tests."""
        print("--- Generating LLM Response for Testing ---")
        prompt = CANDIDATE_PROMPT_TEMPLATE.format(r_code=TEST_R_CODE)
        cls.llm_output = get_ollama_response(prompt)
        print(f"OUTPUT:\n{cls.llm_output}\n---------------------------------------")

    def test_syntax_validity(self):
        """Fail if it uses 'Label' = Value format."""
        passed, msg = SPSSEvaluator.check_value_label_syntax(self.llm_output)
        self.assertTrue(passed, msg)

    def test_hallucinations(self):
        """Fail if it invents commands like !GETDEFS."""
        passed, msg = SPSSEvaluator.check_hallucinations(self.llm_output)
        self.assertTrue(passed, msg)

    def test_completeness(self):
        """Fail if it forgets to translate a variable."""
        passed, msg = SPSSEvaluator.check_variable_coverage(self.llm_output, EXPECTED_VARS)
        self.assertTrue(passed, msg)

    def test_clean_output(self):
        """Fail if Markdown blocks are included (optional)."""
        self.assertNotIn("```", self.llm_output, "Output contains Markdown code blocks, prompt should forbid this.")

if __name__ == '__main__':
    unittest.main()