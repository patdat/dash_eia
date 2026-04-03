#!/usr/bin/env python3
"""
WPS (Weekly Petroleum Status) Data Pipeline — Standalone Entry Point

Usage:
    python main.py           # Run pipeline (skips if already up to date)
    python main.py --force   # Force full redownload
"""

import os
import sys

# Ensure data directories exist
for d in ["data", "data/eia", "data/eia/ingestion", "data/eia/processed", "logs"]:
    os.makedirs(d, exist_ok=True)

from scripts.wps import run_pipeline

if __name__ == "__main__":
    force = "--force" in sys.argv
    run_pipeline(force=force)
