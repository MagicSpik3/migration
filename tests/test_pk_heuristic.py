import unittest
import pandas as pd

class TestPKHeuristic(unittest.TestCase):
    
    def test_primary_key_rule(self):
        """
        Scenario: Determine if we should save the output based on the 'id' column.
        """
        print("\n🧪 Testing Primary Key Heuristic...")

        # 1. The Transformation (calc_delays)
        # It adds a column AND removes a row.
        df_transform = pd.DataFrame({
            "id": ["101", "102"],  # ID Preserved
            "delay": [10, 5]
        })
        
        # 2. The Report (summarize_deaths)
        # It groups data and loses the ID.
        df_report = pd.DataFrame({
            "month": ["Jan", "Feb"],
            "count": [50, 20]
        }) # ID Lost

        # --- THE LOGIC ---
        def should_update_state(df, pk="id"):
            return pk in df.columns

        # Test Transform
        decision_transform = should_update_state(df_transform)
        print(f"   [Transform (Has ID)]: {decision_transform}")
        self.assertTrue(decision_transform, "❌ Failed! Should identify Transform as pipeline update.")

        # Test Report
        decision_report = should_update_state(df_report)
        print(f"   [Report (No ID)]:     {decision_report}")
        self.assertFalse(decision_report, "❌ Failed! Should identify Report as dead-end.")

if __name__ == "__main__":
    unittest.main()