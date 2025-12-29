import pandas as pd
import os

# Define the "True Raw" schema (No derived columns!)
raw_data = {
    "id": ["101", "102", "103", "104", "105", "106"],
    "dor": ["20200115", "20210520", "20191101", "20220310", "20200815", "20211201"], # Raw string dates
    "dod": ["20200220", "20210601", "20230101", "20220315", "20200820", ""],        # Some empty/missing
    "region": ["North", "South", "East", "West", "North", "South"],
    "age": ["68", "45", "72", "34", "80", "29"],                                   # Strings, need casting
    "sex": ["M", "F", "M", "F", "M", "F"],
    "status": ["Deceased", "Deceased", "Deceased", "Deceased", "Deceased", "Active"]
}

# Create DataFrame
df = pd.DataFrame(raw_data)

# Save to the repository root
repo_path = os.path.expanduser("~/git/dummy_spss_repo")
os.makedirs(repo_path, exist_ok=True)
file_path = os.path.join(repo_path, "input_data.csv")

df.to_csv(file_path, index=False)

print(f"✅ Reset {file_path} to TRUE RAW state.")
print("   Columns: " + ", ".join(df.columns))
print("   (Note: 'date_reg', 'date_death', 'delay_days' are purposely MISSING)")