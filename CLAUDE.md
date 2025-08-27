# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Main dashboard application
python index.py

# Full data refresh - updates all modules
python main.py

# Module-specific data updates
python -m src.steo.download_xlsx    # Weekly petroleum data
python -m src.steo.download         # STEO forecast data  
python -m src.cli.main              # Company-level import data
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Architecture Overview

This is a multi-module Dash application for energy market analysis using EIA data. The architecture consists of three main data processing pipelines that feed into a unified dashboard interface.

### Data Processing Modules

**WPS (Weekly Petroleum Status)** - `src/wps/`
- Downloads weekly petroleum data from EIA
- Processes stocks, production, imports data
- Generates derived datasets for line charts and seasonality analysis
- Uses mapping dictionaries to translate EIA series IDs to readable names

**STEO (Short-Term Energy Outlook)** - `src/steo/`
- Processes EIA forecast data with historical tracking
- Creates pivot tables for time series analysis
- Tracks forecast evolution over release dates

**CLI (Company Level Imports)** - `src/cli/`
- Processes company-level crude oil import data
- Categorizes by API gravity and sulfur content
- Provides quality arbitrage and refinery dependency analysis

### Data Storage Pattern

All processed data is stored in optimized formats:
- **Feather format** (`.feather`) for fast DataFrame loading
- **Parquet format** (`.parquet`) for compressed storage
- Located in `data/{module}/` directories

### Caching System

Multi-level caching implemented in `src/utils/cache_*`:
- **Memory cache** with TTL expiration
- **File-based cache** that invalidates on data updates
- **Preload system** for common datasets at startup
- Cache can be managed via API endpoints at `/api/cache/*`

### Page Routing Structure

Pages follow a hierarchical numbering system:
- `page1.py` - Home dashboard
- `page2_*.py` - EIA Weekly (WPS) analysis pages (15 pages)
- `page3_*.py` - EIA DPR drilling productivity pages (10 pages)
- `page4_*.py` - EIA STEO forecast pages (6 pages)
- `page5_*.py` - EIA CLI import analysis pages (10 pages)
- `page6_*.py` - Placeholder for future modules

Each page module must:
1. Define a `layout` variable or function
2. Include Dash callbacks for interactivity
3. Be imported in `index.py` to register routes

### Key Data Mappings

The application relies heavily on mapping dictionaries:
- `src/wps/mapping.py` - Maps EIA series IDs to descriptions
- `src/wps/ag_mapping.py` - AG Grid column definitions
- `lookup/` directory - Contains reference data files

### Adding New Features

When adding new analysis pages:
1. Create page file in `pages/` following naming convention
2. Import in `index.py` with descriptive comment
3. Add navigation entry in sidebar structure
4. Use `src/utils/data_loader.py` for data access with caching

When adding new data sources:
1. Create module in `src/` with download and processing scripts
2. Store processed data in `data/{module}/` 
3. Add update command to `main.py`
4. Document data refresh command in README.md

### Performance Considerations

- Always use cached data loading via `data_loader.py`
- Process data to Feather/Parquet format for production
- Implement callbacks efficiently with minimal data transfer
- Use AG Grid for large tabular displays