"""
PRISM Data Hierarchy — Layer 1: UIO (Units in Operation)
=========================================================
UIO is the denominator for every metric in PRISM.
No GPS figure and no PMS capture rate is meaningful without an accurate UIO count.

Source:    IML vehicle registration data (official, annual)
Authority: Highest — this is the ground truth for fleet size
Updates:   Annual (see data/README.md for beta versioning protocol)

Key surviving parc figures (10-year, used as denominators):
  N75 (NPR75 + NPR88): 8,515 of 12,228 total registered (28.5% attrition)
  N35 (NLR87 + NLR88): 9,818 of 10,919 total registered (9.4% attrition)

WARNING: Do NOT use total registrations as the UIO denominator.
         The surviving parc is the correct base for all calculations.
"""

# Module: UIO Loader
# PRISM — Parts Revenue Intelligence & Sales Monitor
#
# Loads UIO (Units in Operation) data from an Excel file.
# Supports beta/prod file toggle via config.py.

import warnings
import pandas as pd


def load_uio(path: str) -> pd.DataFrame:
    """
    Read a UIO Excel file and return a clean DataFrame.

    Column normalisation applied:
        - All column names lowercased
        - Leading/trailing whitespace stripped from column names
        - String columns have their values stripped of whitespace

    Parameters
    ----------
    path : str
        Relative or absolute path to the UIO .xlsx file.

    Returns
    -------
    pd.DataFrame
        Clean UIO DataFrame. Returns an empty DataFrame (with a warning)
        if the file does not exist or cannot be read.
    """
    import os

    if not os.path.exists(path):
        warnings.warn(
            f"UIO file not found: '{path}'. "
            "Returning empty DataFrame. Check config.py and data/ folder.",
            stacklevel=2,
        )
        return pd.DataFrame()

    try:
        df = pd.read_excel(path, dtype=str)
    except Exception as exc:
        warnings.warn(
            f"Failed to read UIO file '{path}': {exc}. "
            "Returning empty DataFrame.",
            stacklevel=2,
        )
        return pd.DataFrame()

    # Normalise column names
    df.columns = [col.strip().lower() for col in df.columns]

    required = {"distributor_code", "year", "uio_units"}
    if not required.issubset(df.columns):
        # V17 workbook (wide layout on sheet '1.UIO Overview')
        from modules.data_prep import load_uio_from_excel

        return load_uio_from_excel(path)

    # Strip whitespace from all string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Coerce numeric-looking columns to numeric
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        if coerced.notna().sum() > 0.5 * len(df):
            df[col] = coerced

    return df
