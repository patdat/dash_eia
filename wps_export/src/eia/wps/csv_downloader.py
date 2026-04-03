#!/usr/bin/env python3
"""
Fast WPS downloader — parses EIA table9.csv (~1 second) instead of
downloading 6 Excel files (~28 seconds).

Returns the latest week's data as a DataFrame matching the parquet schema:
(date, series_id, value, series, source).
"""

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CSV_URL = "https://ir.eia.gov/wpsr/table9.csv"
MAPPING_CSV = "./config/09_csv_mapping.csv"


def _build_lookup_key(df):
    """Normalize CSV rows and build lookup keys for series ID mapping.

    Mirrors the logic from src/wps/download_csv.py (first_pass + second_pass).
    """
    df = df.copy()

    # Normalize text — keep trailing space on STUB_1 (the mapping expects it)
    df["STUB_1"] = df["STUB_1"].str.lower()
    df["STUB_2"] = df["STUB_2"].str.lower()
    df["STUB_2"] = df["STUB_2"].str.replace("'", "", regex=False)
    df["STUB_2"] = df["STUB_2"].str.replace("&", "and", regex=False)

    # Location detection
    locations = {
        "p1": "east coast (padd 1)",
        "p2": "midwest (padd 2)",
        "p3": "gulf coast (padd 3)",
        "p4": "rocky mountain (padd 4)",
        "p5": "west coast (padd 5)",
        "p45": "padds 4 and 5",
        "p1a": "new england (padd 1a)",
        "p1b": "central atlantic (padd 1b)",
        "p1c": "lower atlantic (padd 1c)",
        "us": "us",
    }
    locations_inv = {v: k for k, v in locations.items()}

    df["location"] = np.where(
        df["STUB_2"].isin(list(locations.values())), df["STUB_2"], "us"
    )
    df["category"] = np.where(df["location"] == "us", df["STUB_2"], None)
    df["category"] = df["category"].ffill()
    df["location"] = df["location"].map(locations_inv)

    # Build lookup key
    df["lookup"] = df["STUB_1"] + df["location"] + df["category"]

    return df


def download_and_parse():
    """Download table9.csv, parse, and return the latest week's data.

    Returns:
        (latest_date, DataFrame[date, series_id, value, series, source])

    Raises:
        Exception if download or parsing fails.
    """
    logger.info("Downloading table9.csv...")
    raw = pd.read_csv(CSV_URL, encoding="ISO-8859-1")
    logger.info("Downloaded %d rows", len(raw))

    # The latest week is column index 2 (after STUB_1, STUB_2)
    date_col = raw.columns[2]
    latest_date = pd.to_datetime(date_col, format="%m/%d/%y")
    logger.info("Latest date: %s", latest_date.date())

    # Track which rows are stocks (STUB_1 contains "million barrels")
    is_stock = raw["STUB_1"].str.contains("million barrels", case=False, na=False)

    # Clean the value column
    values = raw[date_col].astype(str).str.replace(",", "", regex=False)
    values = pd.to_numeric(values, errors="coerce")

    # Build lookup keys
    keyed = _build_lookup_key(raw)

    # Load mapping
    mapping = pd.read_csv(MAPPING_CSV)

    # Merge to get series_id
    keyed["value"] = values
    keyed["is_stock"] = is_stock
    merged = mapping.merge(keyed, on="lookup", how="left")

    # Drop rows with no value
    merged = merged.dropna(subset=["value"])
    # Drop duplicates (keep first occurrence per series_id)
    merged = merged.drop_duplicates(subset=["id"])

    # Scale stocks: CSV is in millions, parquet is in thousands
    merged.loc[merged["is_stock"], "value"] = merged.loc[merged["is_stock"], "value"] * 1000

    # Round: stocks to 0, everything else to 0
    merged["value"] = merged["value"].round(0)

    # Build output DataFrame matching parquet schema
    result = pd.DataFrame({
        "date": latest_date,
        "series_id": merged["id"].str.upper(),
        "value": merged["value"].values,
        "series": "",  # not needed for report
        "source": merged["STUB_1"].str.strip().values if "STUB_1" in merged.columns else "",
    })

    logger.info("Parsed %d series for %s", len(result), latest_date.date())
    return latest_date, result
