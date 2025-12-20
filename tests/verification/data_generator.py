import pandas as pd
import numpy as np
import random

def generate_synthetic_deaths_data(rows=100):
    """
    Generates a synthetic dataframe that mimics the 'weekly.deaths' input.
    """
    # These match the valid levels you just verified!
    sexes = ["Male", "Female"]
    regions = ["North East", "North West", "London", "South East"]
    ages = ["Under 1", "15 to 19", "45 to 49", "85 to 89"]
    
    data = {
        "sex": [random.choice(sexes) for _ in range(rows)],
        "region": [random.choice(regions) for _ in range(rows)],
        "agegrp_5yr": [random.choice(ages) for _ in range(rows)],
        "deaths": np.random.randint(0, 100, size=rows),
        "week_number": np.random.randint(1, 52, size=rows),
        "year": [2023] * rows
    }
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df = generate_synthetic_deaths_data()
    df.to_csv("tests/verification/synthetic_input.csv", index=False)
    print("Created synthetic_input.csv")