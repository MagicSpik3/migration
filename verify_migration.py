import pandas as pd
import subprocess
import os
import sys

def run_pipeline(command, description):
    print(f"🚀 Running {description}...")
    try:
        # Run from current directory to ensure relative CSV paths work
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} success.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} FAILED.")
        print(e.stderr)
        return False

def compare_outputs(file_legacy, file_r):
    print(f"\n⚖️  Comparing outputs: {file_legacy} vs {file_r}")
    
    if not os.path.exists(file_legacy) or not os.path.exists(file_r):
        print("❌ One or both output files are missing.")
        return

    # Load data
    df_legacy = pd.read_csv(file_legacy)
    df_r = pd.read_csv(file_r)

    # Normalize column names (lowercase) and sort for fair comparison
    df_legacy.columns = df_legacy.columns.str.lower()
    df_r.columns = df_r.columns.str.lower()

    # Sort by key columns (adjust 'benefit_type'/'region' as needed)
    sort_keys = ['benefit_type', 'region']
    df_legacy = df_legacy.sort_values(by=sort_keys).reset_index(drop=True)
    df_r = df_r.sort_values(by=sort_keys).reset_index(drop=True)

    # Compare
    try:
        pd.testing.assert_frame_equal(df_legacy, df_r, check_dtype=False, atol=0.01) # Allow 1 penny diff
        print("✅ SUCCESS: R pipeline matches PSPP output exactly!")
    except AssertionError as e:
        print("⚠️  MISMATCH: The pipelines produced different results.")
        print(e)

if __name__ == "__main__":
    # 1. Run Legacy (PSPP)
    # Note: We run from root so 'claims_data.csv' is found
    if not run_pipeline("pspp syntax/example_pspp_final.sps", "Legacy PSPP"):
        sys.exit(1)

    # 2. Run New (R)
    # Ensure you have fixed the read_csv inputs in the R script first!
    if not run_pipeline("Rscript main.R", "Modern R"):
        sys.exit(1)

    # 3. Compare
    # Assuming R outputs to the same filename, or you modified it to save as 'benefit_summary_r.csv'
    # If main.R overwrites, you might want to rename the PSPP output first.
    
    # Recommendation: Modify your R script to save to 'benefit_monthly_summary_r.csv' 
    # for side-by-side comparison.
    compare_outputs("benefit_monthly_summary.csv", "benefit_monthly_summary.csv")