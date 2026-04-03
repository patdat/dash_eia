#!/usr/bin/env python3
"""
WPS (Weekly Petroleum Status) Data Pipeline
Release Check → Ingest → Process
"""

import logging

from src.eia.wps.ingester import main as ingest_wps_data
from src.eia.wps.processor import main as process_wps_data
from src.eia.wps.release_checker import is_new_data_available, mark_downloaded
from src.eia.utils.logging_setup import setup_pipeline_logging


logger = logging.getLogger(__name__)


def run_pipeline(force=False):
    """Run the complete WPS data pipeline"""
    log_path = setup_pipeline_logging("wps")
    logger.info("Log file: %s", log_path)

    logger.info("=" * 80)
    logger.info("EIA WPS Data Pipeline%s", " (--force)" if force else "")
    logger.info("=" * 80)

    try:
        logger.info("[0/2] Checking for new WPS release...")
        if not is_new_data_available(force=force):
            logger.info("✓ WPS pipeline completed — no new release")
            return

        logger.info("[1/2] Ingesting WPS data...")
        data_changed = ingest_wps_data(force=force)

        if not data_changed:
            logger.info("No new data — skipping processing.")
        else:
            logger.info("[2/2] Processing WPS data...")
            process_wps_data()

        mark_downloaded()
        logger.info("✓ WPS pipeline completed successfully")
    except Exception as exc:
        logger.error("✗ WPS pipeline failed: %s", exc)
        raise
    finally:
        logger.info("=" * 80)


if __name__ == '__main__':
    run_pipeline()
