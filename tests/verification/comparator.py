import pandas as pd
import numpy as np
import logging

def compare_outputs(r_csv_path, spss_csv_path, tolerance=1e-5):
    """
    Compares two CSV files for equivalence.
    """
    try:
        # Load data
        # dtype=str prevents pandas from inferring types differently for R/SPSS
        df_r = pd.read_csv(r_csv_path)
        df_spss = pd.read_csv(spss_csv_path)
    except FileNotFoundError as e:
        return False, f"Missing output file: {e}"

    # 1. Check Column Alignment
    # SPSS lowercases variables often; normalize to lowercase for comparison
    df_r.columns = df_r.columns.str.lower()
    df_spss.columns = df_spss.columns.str.lower()

    common_cols = list(set(df_r.columns) & set(df_spss.columns))
    if not common_cols:
        return False, "No common columns found between R and SPSS outputs."

    # Filter to common columns and sort to ensure alignment
    df_r = df_r[common_cols].sort_values(by=common_cols[0]).reset_index(drop=True)
    df_spss = df_spss[common_cols].sort_values(by=common_cols[0]).reset_index(drop=True)

    # 2. Check Dimensions
    if df_r.shape != df_spss.shape:
        return False, f"Shape mismatch: R{df_r.shape} vs SPSS{df_spss.shape}"

    # 3. Numeric Comparison
    mismatches = []
    for col in common_cols:
        # Attempt numeric conversion
        try:
            r_vals = pd.to_numeric(df_r[col])
            spss_vals = pd.to_numeric(df_spss[col])
            
            # Check for closeness (floating point tolerance)
            if not np.allclose(r_vals, spss_vals, rtol=tolerance, equal_nan=True):
                mismatches.append(col)
        except ValueError:
            # If not numeric, do exact string match
            if not df_r[col].equals(df_spss[col]):
                mismatches.append(col)

    if mismatches:
        return False, f"Data mismatch in columns: {mismatches}"

    return True, "Outputs are identical."