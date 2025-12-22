import pandas as pd
import os
import json

def seed_repo_data(manifest_path="migration_manifest.json"):
    # 1. Find the Repo Root from the manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    first_r_file = manifest[0]['r_file']
    repo_root = os.path.dirname(os.path.dirname(first_r_file))
    
    target_csv = os.path.join(repo_root, "input_data.csv")
    
    # 2. Generate Data (Same logic as verification)
    print(f"🌱 Seeding data to {target_csv}...")
    df = pd.DataFrame({
        'dor': ["20230105", "20221231", "20240229", "20230520"],
        'dod': ["20230101", "20221225", "20240228", "20230510"]
    })
    
    df.to_csv(target_csv, index=False)
    print("✅ Data Seeded.")

if __name__ == "__main__":
    seed_repo_data()