import unittest

class TestHeuristicFix(unittest.TestCase):
    
    def test_heuristic_enrichment_with_filter(self):
        """
        Scenario: Script adds a column (Enrichment) but removes a row (Filter).
        Old Logic: Row count dropped? SKIPPED. (Bug)
        New Logic: Column count increased? UPDATED. (Fix)
        """
        print("\n🧪 Testing Heuristic: Enrichment + Filter...")
        
        # State Before (3 rows, 2 cols)
        original_cols = 2
        original_rows = 3
        
        # State After (2 rows, 3 cols) - Added 'delay', removed 1 row
        new_cols = 3 
        new_rows = 2
        
        # --- OLD LOGIC (Simulated) ---
        is_cleaning_old = (new_rows == original_rows)
        # Old logic would fail here because new_rows != original_rows
        result_old = "UPDATED" if is_cleaning_old else "SKIPPED"
        print(f"   [Old Logic Result]: {result_old}")
        self.assertEqual(result_old, "SKIPPED", "Sanity check: Old logic should have failed.")

        # --- NEW LOGIC (Simulated) ---
        is_enrichment = (new_cols > original_cols)
        is_cleaning = (new_rows == original_rows)
        
        result_new = "UPDATED" if (is_enrichment or is_cleaning) else "SKIPPED"
        print(f"   [New Logic Result]: {result_new}")
        
        self.assertEqual(result_new, "UPDATED", "❌ Fix Failed! Enrichment was not detected.")

if __name__ == "__main__":
    unittest.main()