import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.ollama_client import get_ollama_response
from src.specs.prompts import ARCHITECT_PROMPT

class TestFailureReproduction(unittest.TestCase):

    def generate_code(self, spec, schema):
        """Helper to simulate the Architect."""
        full_prompt = ARCHITECT_PROMPT.format(
            target_name="test_func",
            spec_content=spec,
            columns=schema,
            glossary="No specific glossary terms."
        )
        # Force deterministic output
        return get_ollama_response(full_prompt).strip()

    def test_fix_calc_delays_hallucination(self):
        """
        Problem: Architect tries to mutate 'date_reg' from 'date_reg', 
                 but the input column is actually 'dor'.
        Goal: Ensure it uses the SCHEMA column ('dor') as the source.
        """
        print("\n🧪 Reproducing 'calc_delays' Hallucination...")
        spec = "Calculate 'date_reg' by parsing the 'dor' column."
        # The Schema ONLY has 'dor', not 'date_reg'
        schema = "`id`, `dor`, `region`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output]: {code.replace(chr(10), ' ')[:80]}...")
        
        # FAIL if it tries to read 'date_reg' before creating it
        self.assertNotIn("ymd(date_reg)", code, "❌ Architect hallucinated 'date_reg' as input!")
        
        # PASS if it reads 'dor'
        self.assertIn("dor", code, "❌ Architect ignored the input column 'dor'.")

    def test_fix_summarize_deaths_zombie_str_sub(self):
        """
        Problem: Architect persists in using str_sub(date, 1, 8) despite bans.
        Goal: Ensure it uses simple ymd(date_col).
        """
        print("\n🧪 Reproducing 'summarize_deaths' Zombie str_sub...")
        spec = "Parse 'date_death' and count deaths per month."
        schema = "`id`, `date_death`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output]: {code.replace(chr(10), ' ')[:80]}...")
        
        # FAIL if str_sub appears
        self.assertNotIn("str_sub", code, "❌ The Zombie Lives! Architect used str_sub on a date.")
        
        # PASS if it uses ymd directly
        self.assertIn("ymd(date_death)", code, "❌ Architect failed to use clean ymd() parsing.")

    def test_fix_complex_logic_dependency(self):
        """
        Problem: Optimizer crashes because it tests scripts in isolation 
                 without the columns created by previous scripts.
        Goal: This is harder to fix in the prompt, but we must verify 
              the Architect at least *assumes* the column exists if told so.
        """
        print("\n🧪 Reproducing 'complex_logic' Dependency...")
        spec = "Filter rows where delay_days > 0."
        
        # CRITICAL: We pretend 'delay_days' is in the schema here.
        # If this passes, the issue is purely in the *Orchestrator* (run_migration.py),
        # not the Architect.
        schema = "`id`, `delay_days`"
        
        code = self.generate_code(spec, schema)
        print(f"   [Output]: {code.replace(chr(10), ' ')[:80]}...")
        
        self.assertIn("delay_days", code)

if __name__ == "__main__":
    unittest.main()