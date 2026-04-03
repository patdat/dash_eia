#!/usr/bin/env python3
"""
WPS (Weekly Petroleum Status) Data Pipeline
Fast CSV path → Excel fallback → Process
"""

import logging
import os

import pandas as pd

from src.eia.wps.csv_downloader import download_and_parse as csv_download
from src.eia.wps.ingester import main as ingest_wps_data
from src.eia.wps.processor import main as process_wps_data
from src.eia.wps.release_checker import is_new_data_available, mark_downloaded
from src.eia.utils.logging_setup import setup_pipeline_logging

logger = logging.getLogger(__name__)

PARQUET_PATH = "./data/eia/ingestion/wps.parquet"


def _try_fast_csv():
    """Attempt the fast CSV path.

    Returns:
        True if fast path succeeded (data appended or already up to date).
        False if we need the Excel fallback (gap detected or no existing data).
    """
    try:
        csv_date, csv_df = csv_download()
    except Exception as exc:
        logger.warning("Fast CSV download failed: %s — falling back to Excel", exc)
        return False

    if not os.path.exists(PARQUET_PATH):
        logger.info("No existing parquet — need full Excel rebuild")
        return False

    existing = pd.read_parquet(PARQUET_PATH)
    existing["date"] = pd.to_datetime(existing["date"])
    parquet_max = existing["date"].max()

    gap_days = (csv_date - parquet_max).days
    logger.info(
        "Parquet max date: %s | CSV date: %s | Gap: %d days",
        parquet_max.date(), csv_date.date(), gap_days,
    )

    if gap_days <= 0:
        logger.info("Already up to date — nothing to do")
        return "up_to_date"

    if gap_days == 7:
        logger.info("Fast path: appending %d rows for %s", len(csv_df), csv_date.date())
        combined = pd.concat([existing, csv_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date", "series_id"], keep="last")
        combined = combined.sort_values(["date", "series_id"])

        os.makedirs(os.path.dirname(PARQUET_PATH), exist_ok=True)
        combined.to_parquet(PARQUET_PATH, index=False)
        logger.info("Saved parquet: %d rows", len(combined))
        return True

    logger.warning(
        "Gap of %d days detected (expected 7) — falling back to Excel rebuild",
        gap_days,
    )
    return False


def run_pipeline(force=False):
    """Run the complete WPS data pipeline."""
    log_path = setup_pipeline_logging("wps")
    logger.info("Log file: %s", log_path)

    logger.info("=" * 80)
    logger.info("EIA WPS Data Pipeline%s", " (--force)" if force else "")
    logger.info("=" * 80)

    try:
        logger.info("[0] Checking for new WPS release...")
        if not is_new_data_available(force=force):
            logger.info("✓ No new release — done")
            return

        data_changed = False

        # Try fast CSV path first (unless --force)
        if not force:
            logger.info("[1] Trying fast CSV path...")
            result = _try_fast_csv()
            if result == "up_to_date":
                logger.info("✓ Already up to date — done")
                mark_downloaded()
                return
            elif result:
                data_changed = True
            else:
                logger.info("[1] Fast path unavailable — using Excel fallback...")
                data_changed = ingest_wps_data(force=False)
        else:
            logger.info("[1] --force: using Excel path...")
            data_changed = ingest_wps_data(force=True)

        if data_changed:
            logger.info("[2] Processing data...")
            process_wps_data()
        else:
            logger.info("No new data — skipping processing")

        mark_downloaded()
        logger.info("✓ WPS pipeline completed successfully")
    except Exception as exc:
        logger.error("✗ WPS pipeline failed: %s", exc)
        raise
    finally:
        logger.info("=" * 80)


if __name__ == "__main__":
    run_pipeline()
