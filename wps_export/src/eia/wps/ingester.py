#!/usr/bin/env python3
"""
WPS Ingester — downloads Excel files to memory, parses inline, applies series
processing, and saves parquet + CSV. No disk storage of .xls files.

Modeled on src/eia/psm/ingester.py. Uses psw01.xls as anchor for freshness.
"""

import csv
import io
import json
import logging
import os
import re
from datetime import datetime, date
from typing import Optional, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MANIFEST_CSV = './config/wps_download_list.csv'
OUTPUT_PARQUET = './data/eia/ingestion/wps.parquet'
OUTPUT_PARQUET_PROCESSED = './data/eia/processed/wps.parquet'
TRACKER_JSON = './data/eia/ingestion/wps_tracker.json'
DOWNLOAD_TIMEOUT = 30
ANCHOR_FILENAME = 'psw01.xls'
MIN_DATE_YEAR = 2014
CSV_MIN_DATE = '2025-01-01'

FILTER_TERMS = ['4WK', '4-WEEK', '4-WEEK AVG', 'AVERAGE', 'AVG']


# ---------------------------------------------------------------------------
# Tracker (freshness tracking)
# ---------------------------------------------------------------------------
def load_tracker() -> dict:
    if os.path.exists(TRACKER_JSON):
        with open(TRACKER_JSON, "r") as f:
            return json.load(f)
    return {"anchor_date": None, "last_run": None, "urls": {}}


def save_tracker(tracker: dict) -> None:
    tmp = TRACKER_JSON + ".tmp"
    with open(tmp, "w") as f:
        json.dump(tracker, f, indent=2, default=str)
    os.replace(tmp, TRACKER_JSON)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def load_manifest() -> list:
    with open(MANIFEST_CSV, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def download_to_memory(url: str) -> io.BytesIO:
    resp = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
    resp.raise_for_status()
    buf = io.BytesIO()
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            buf.write(chunk)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Excel metadata extraction
# ---------------------------------------------------------------------------
def extract_latest_date_bytes(buf: io.BytesIO, filename: str) -> date:
    """Extract the latest date from an in-memory Excel file."""
    xls = pd.ExcelFile(buf, engine="xlrd")
    data_sheets = [s for s in xls.sheet_names if 'Data' in s]
    if not data_sheets:
        data_sheets = [xls.sheet_names[0]]

    for sheet in data_sheets:
        df = xls.parse(sheet_name=sheet, header=None, usecols=[0], skiprows=3)
        col = df[0].dropna()
        # xlrd returns dates as datetime64 already; coerce any stragglers
        if not pd.api.types.is_datetime64_any_dtype(col):
            col = pd.to_datetime(col, errors='coerce').dropna()
        dates = col[(col.dt.year >= 1900) & (col.dt.year <= 2100)]
        if not dates.empty:
            return dates.max().date()

    raise ValueError(f"Cannot determine latest date for {filename}")


def read_contents_description(buf: io.BytesIO, filename: str) -> str:
    """Read the file description from cell B3 of the 'Contents' tab."""
    try:
        xls = pd.ExcelFile(buf, engine="xlrd")
        contents_sheets = [s for s in xls.sheet_names if "contents" in s.lower()]
        if not contents_sheets:
            return ""
        df = xls.parse(sheet_name=contents_sheets[0], header=None, nrows=3, usecols=[1])
        val = df.iloc[2, 0] if len(df) >= 3 else ""
        return str(val).strip() if pd.notna(val) else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Series processing functions (moved from compiler.py)
# ---------------------------------------------------------------------------
def abbreviate_series_name(name):
    """Create abbreviated version of series name."""
    if pd.isna(name):
        return ''

    name_str = str(name).upper()

    replacements = {
        'EAST COAST (PADD 1)': 'P1',
        'MIDWEST (PADD 2)': 'P2',
        'GULF COAST (PADD 3)': 'P3',
        'ROCKY MOUNTAIN (PADD 4)': 'P4',
        'WEST COAST (PADD 5)': 'P5',
        'PADD 1': 'P1',
        'PADD 2': 'P2',
        'PADD 3': 'P3',
        'PADD 4': 'P4',
        'PADD 5': 'P5',
        'UNITED STATES': 'US',
        'THOUSAND BARRELS PER DAY': 'KBD',
        'THOUSAND BARRELS': 'KB',
        'THOUSAND BARRELS PER CALENDAR DAY': 'KBCD',
        'GASOLINE BLENDING COMPONENTS': 'GAS BLEND',
        'DISTILLATE FUEL OIL': 'DFO',
        'MOTOR GASOLINE': 'MOGAS',
        'RESIDUAL FUEL OIL': 'RFO',
        'KEROSENE-TYPE JET FUEL': 'JET',
        'PROPANE/PROPYLENE': 'PROPANE',
        'CRUDE OIL': 'CRD',
        'ENDING STOCKS': 'STK',
        'EXCLUDING': 'EXCL',
        'INCLUDING': 'INCL',
        'COMMERCIAL': 'COMM',
        'STRATEGIC PETROLEUM RESERVE': 'SPR',
        'REFINERY': 'REF',
        'REFINER': 'REF',
        'PRODUCTION': 'PROD',
        'IMPORTS': 'IMP',
        'EXPORTS': 'EXP',
        'SUPPLIED': 'SUPP',
        'UTILIZATION': 'UTIL',
        'NET INPUT': 'NET IN',
        'PERCENT': 'PCT',
        '4-WEEK AVG': '4WK',
        'WEEKLY': 'WK',
    }

    result = name_str
    for old, new in replacements.items():
        result = result.replace(old, new)

    result = re.sub(r'\s*\([^)]+\)\s*$', '', result)
    result = ' '.join(result.split())
    return result


def extract_unit(series_name):
    """Extract unit from series name."""
    name_lower = series_name.lower()

    unit_mapping = {
        '(thousand barrels per day)': 'KBD',
        '(thousand barrels per calendar day)': 'KBD',
        '(thousand barrels)': 'KB',
        'thousand barrels': 'KB',
        'percent': 'PCT',
        'days': 'DAYS',
        'degrees': 'DEG',
        'dollars per gallon': 'DPG',
        'cents per gallon': 'CPG',
    }

    for keyword, unit in unit_mapping.items():
        if keyword in name_lower:
            return unit
    return None


def extract_product_category_wps(
    series_desc: str,
    product_code: str = None,
    process_code: str = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract product, category, and subcategory from WPS series description."""
    if pd.isna(series_desc):
        return None, None, None

    clean_desc = str(series_desc).strip()
    product = None
    category = None
    subcategory = None

    category_patterns = {
        'STK': r'\b(stocks?|ending stocks?)\b',
        'PROD': r'\b(production|produced|refinery output)\b',
        'IMP': r'\b(imports?)\b',
        'EXP': r'\b(exports?)\b',
        'SUPP': r'\b(supplied|product supplied)\b',
        'RUNS': r'\b(runs?|refinery runs?|crude runs?)\b',
        'INPUTS': r'\b(inputs?|refinery inputs?)\b',
        'PRICE': r'\b(price|prices|retail)\b',
        'UTIL': r'\b(utilization|capacity)\b',
        'ADJ': r'\b(adjustment)\b',
    }

    desc_lower = clean_desc.lower()
    for cat_code, pattern in category_patterns.items():
        if re.search(pattern, desc_lower):
            category = cat_code
            break

    product_patterns = [
        (r'\b(crude oil|crude)\b', 'CRUDE'),
        (r'\b(motor gasoline|gasoline|mogas)\b', 'MOGAS'),
        (r'\b(distillate fuel oil|distillate|dfo)\b', 'DFO'),
        (r'\b(jet fuel|kerosene-type jet fuel|jet)\b', 'JET'),
        (r'\b(residual fuel oil|residual|rfo)\b', 'RFO'),
        (r'\b(propane)\b', 'PROPANE'),
        (r'\b(ethanol)\b', 'ETHANOL'),
        (r'\b(diesel fuel|diesel)\b', 'DIESEL'),
        (r'\b(fuel ethanol)\b', 'FUEL_ETHANOL'),
        (r'\b(total petroleum)\b', 'TOT_PET'),
        (r'\b(other oils)\b', 'OTHER_OILS'),
        (r'\b(unfinished oils)\b', 'UNF_OILS'),
        (r'\b(ngl|natural gas liquids)\b', 'NGL'),
        (r'\b(lpg|liquefied petroleum gases)\b', 'LPG'),
    ]

    for pattern, prod_code in product_patterns:
        if re.search(pattern, desc_lower):
            product = prod_code
            break

    if not product and product_code:
        product = str(product_code).upper()

    subcategory_patterns = [
        (r'padd 1[abc]?', 'PADD1'),
        (r'padd 2', 'PADD2'),
        (r'padd 3', 'PADD3'),
        (r'padd 4', 'PADD4'),
        (r'padd 5', 'PADD5'),
        (r'east coast', 'EAST_COAST'),
        (r'midwest', 'MIDWEST'),
        (r'gulf coast', 'GULF_COAST'),
        (r'rocky mountain', 'ROCKY_MTN'),
        (r'west coast', 'WEST_COAST'),
        (r'u\.s\.', 'US'),
        (r'cushing', 'CUSHING'),
        (r'spr', 'SPR'),
    ]

    for pattern, subcat_code in subcategory_patterns:
        if re.search(pattern, desc_lower):
            subcategory = subcat_code
            break

    return product, category, subcategory


# ---------------------------------------------------------------------------
# Excel parsing (single in-memory file)
# ---------------------------------------------------------------------------
def parse_wps_excel(buf: io.BytesIO, filename: str) -> Optional[pd.DataFrame]:
    """Parse a single WPS Excel file from memory into a long-format DataFrame."""
    try:
        xls = pd.ExcelFile(buf, engine="xlrd")
    except Exception:
        logger.error("  Cannot open %s", filename)
        return None

    all_data = []
    for sheet_name in xls.sheet_names:
        if 'Data' not in sheet_name:
            continue

        df = pd.read_excel(buf, sheet_name=sheet_name, header=None, engine="xlrd")
        if df.shape[0] < 4 or df.shape[1] < 2:
            continue

        # Row 1 (iloc[1]): series codes
        series_codes = df.iloc[1, 1:].dropna().tolist()
        # Row 2 (iloc[2]): series descriptions
        series_descriptions = df.iloc[2, 1:].dropna().tolist()
        min_len = min(len(series_codes), len(series_descriptions))

        # Row 3+ (iloc[3:]): date column + value columns
        for i in range(min_len):
            if i + 1 >= df.shape[1]:
                continue
            date_col = df.iloc[3:, 0]
            values = df.iloc[3:, i + 1]

            for date_val, value_val in zip(date_col, values):
                if pd.isna(date_val) or pd.isna(value_val):
                    continue
                try:
                    parsed_date = pd.to_datetime(date_val)
                    if parsed_date.year >= MIN_DATE_YEAR:
                        all_data.append({
                            'date': parsed_date,
                            'series_id': str(series_codes[i]),
                            'series': str(series_descriptions[i]),
                            'value': float(value_val),
                            'source': filename,
                        })
                except (ValueError, TypeError):
                    continue

    if all_data:
        return pd.DataFrame(all_data)
    return None


# ---------------------------------------------------------------------------
# Series processing — lean version
# ---------------------------------------------------------------------------
def apply_series_processing(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out 4-week averages and keep core columns only.

    The report generator has its own TABLE_DEFS mapping, so we skip the
    heavy metadata extraction (product/category/subcategory, abbreviation,
    location columns) to keep the pipeline fast.
    """
    # Filter out 4-week averages
    mask = pd.Series(True, index=df.index)
    for term in FILTER_TERMS:
        mask = mask & (~df['series'].str.contains(term, case=False, na=False))
    df = df[mask]

    # Drop NA values
    df = df.dropna(subset=['value'])

    # Keep only the columns the report needs
    df = df[['date', 'series_id', 'series', 'value', 'source']].copy()

    # Uppercase series_id for consistent matching
    df['series_id'] = df['series_id'].astype(str).str.strip().str.upper()

    # Sort
    df = df.sort_values(['date', 'series_id'])

    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(force=False) -> bool:
    """Download WPS Excel files to memory, parse, process, and save.
    Returns True if data changed, False otherwise."""

    rows = load_manifest()
    if not rows:
        logger.error("Manifest %s is empty", MANIFEST_CSV)
        return False

    tracker = load_tracker()
    if force:
        logger.info("--force: clearing tracker to redownload all files")
        tracker["urls"] = {}
    tracker["last_run"] = datetime.now().isoformat()

    # --- Anchor phase: download psw01.xls to determine latest date -----------
    anchor_url = None
    for row in rows:
        if ANCHOR_FILENAME in row["url"]:
            anchor_url = row["url"]
            break
    if anchor_url is None:
        anchor_url = rows[0]["url"]

    anchor_filename = anchor_url.split("/")[-1]
    logger.info("=" * 60)
    logger.info("Downloading anchor: %s", anchor_filename)

    anchor_buf = download_to_memory(anchor_url)
    anchor_date = extract_latest_date_bytes(io.BytesIO(anchor_buf.getvalue()), anchor_filename)
    anchor_date_str = str(anchor_date)
    logger.info("Anchor latest date: %s", anchor_date)
    logger.info("=" * 60)

    tracker["anchor_date"] = anchor_date_str

    # Parse anchor file
    new_frames = []
    anchor_df = parse_wps_excel(io.BytesIO(anchor_buf.getvalue()), anchor_filename)
    if anchor_df is not None:
        new_frames.append(anchor_df)
        anchor_series = anchor_df["series_id"].nunique()
    else:
        anchor_series = 0

    anchor_buf.seek(0)
    anchor_desc = read_contents_description(io.BytesIO(anchor_buf.getvalue()), anchor_filename)

    anchor_id_name = dict(zip(anchor_df["series_id"], anchor_df["series"])) if anchor_df is not None else {}
    tracker.setdefault("urls", {})[anchor_url] = {
        "filename": anchor_filename,
        "last_date": anchor_date_str,
        "last_downloaded": tracker["last_run"],
        "status": "ok",
        "contents": anchor_desc,
        "series_count": anchor_series,
        "series_id_name": anchor_id_name,
    }

    # Load existing parquet for incremental merge
    existing_df = None
    if os.path.exists(OUTPUT_PARQUET):
        existing_df = pd.read_parquet(OUTPUT_PARQUET)
        logger.info("Loaded existing wps.parquet: %d rows", len(existing_df))

    save_tracker(tracker)

    # --- Download + parse loop -----------------------------------------------
    downloaded = 1  # anchor already downloaded
    skipped = 0
    failed = 0
    max_fname_len = max(len(row["url"].split("/")[-1]) for row in rows)

    # Log anchor
    logger.info("[1/%d] %s | Max Date = %s | Series = %3d | %s",
                len(rows), anchor_filename.ljust(max_fname_len), anchor_date_str,
                anchor_series, anchor_desc)

    for idx, row in enumerate(rows, start=1):
        url = row["url"]
        filename = url.split("/")[-1]

        if url == anchor_url:
            continue

        # Check tracker for freshness
        entry = tracker.get("urls", {}).get(url, {})
        if entry.get("last_date") == anchor_date_str and entry.get("status") == "ok":
            skipped += 1
            continue

        try:
            buf = download_to_memory(url)
            df = parse_wps_excel(io.BytesIO(buf.getvalue()), filename)
            if df is not None:
                new_frames.append(df)

            # Extract metadata for logging
            try:
                file_date = str(extract_latest_date_bytes(io.BytesIO(buf.getvalue()), filename))
            except Exception:
                file_date = anchor_date_str

            series_count = df["series_id"].nunique() if df is not None else 0
            description = read_contents_description(io.BytesIO(buf.getvalue()), filename)

            logger.info("[%d/%d] %s | Max Date = %s | Series = %3d | %s",
                        idx, len(rows), filename.ljust(max_fname_len), file_date,
                        series_count, description)

            series_id_name = dict(zip(df["series_id"], df["series"])) if df is not None else {}
            tracker.setdefault("urls", {})[url] = {
                "filename": filename,
                "last_date": file_date,
                "last_downloaded": tracker["last_run"],
                "status": "ok",
                "contents": description,
                "series_count": series_count,
                "series_id_name": series_id_name,
            }
            tracker["urls"][url].pop("error", None)
            tracker["urls"][url].pop("fail_count", None)

            downloaded += 1
        except Exception as exc:
            logger.error("[%d/%d] %s | FAILED: %s",
                         idx, len(rows), filename.ljust(max_fname_len), exc)
            prev = tracker.get("urls", {}).get(url, {})
            tracker.setdefault("urls", {})[url] = {
                "filename": filename,
                "last_date": prev.get("last_date"),
                "last_downloaded": prev.get("last_downloaded"),
                "status": "failed",
                "error": str(exc),
                "fail_count": prev.get("fail_count", 0) + 1,
                "contents": prev.get("contents", ""),
                "series_count": prev.get("series_count", 0),
                "series_id_name": prev.get("series_id_name", {}),
            }
            failed += 1

        save_tracker(tracker)

    # --- Merge + process -----------------------------------------------------
    logger.info("-" * 60)

    if not new_frames:
        logger.info("No new data downloaded.")
        return False

    new_df = pd.concat(new_frames, ignore_index=True)
    logger.info("New data: %d rows from %d files", len(new_df), len(new_frames))

    if existing_df is not None and not existing_df.empty:
        # Remove rows from re-downloaded sources
        refreshed_sources = new_df["source"].unique()
        keep = existing_df[~existing_df["source"].isin(refreshed_sources)]
        # Apply series processing to new data, then merge
        processed_new = apply_series_processing(new_df)
        combined = pd.concat([keep, processed_new], ignore_index=True)
    else:
        combined = apply_series_processing(new_df)

    # Deduplicate
    combined = combined.drop_duplicates(subset=["date", "series_id"], keep="last")

    # Compare against existing — skip save if data is unchanged
    if existing_df is not None and not existing_df.empty:
        compare_cols = ["date", "series_id", "value"]
        old_key = set(existing_df[compare_cols].itertuples(index=False, name=None))
        new_key = set(combined[compare_cols].itertuples(index=False, name=None))
        if old_key == new_key:
            logger.info("Data unchanged — skipping save.")
            logger.info("Downloaded: %d | Skipped: %d | Failed: %d", downloaded, skipped, failed)
            return False

    # Save parquet
    os.makedirs(os.path.dirname(OUTPUT_PARQUET), exist_ok=True)
    combined.to_parquet(OUTPUT_PARQUET, index=False)
    logger.info("Saved wps.parquet: %d rows", len(combined))

    # Save processed parquet (2025+ only)
    os.makedirs(os.path.dirname(OUTPUT_PARQUET_PROCESSED), exist_ok=True)
    df_recent = combined[combined['date'] >= CSV_MIN_DATE]
    df_recent.to_parquet(OUTPUT_PARQUET_PROCESSED, engine="pyarrow", compression="gzip", index=False)

    # Summary
    logger.info("Downloaded: %d | Skipped: %d | Failed: %d", downloaded, skipped, failed)
    logger.info("Date range: %s to %s", combined['date'].min(), combined['date'].max())
    logger.info("Unique series: %d", combined['series_id'].nunique())
    return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
