# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python index.py                     # Dashboard at http://localhost:8050
python main.py                      # Full data refresh (all modules)
```

### Module-Specific Data Updates
```bash
python -m src.wps.download_xlsx     # Weekly petroleum data (WPS)
python -m src.steo.download         # STEO forecast data
python -m src.cli.main              # Company-level import data
python -m src.cli.download          # CLI raw download
```

### Dependencies
```bash
pip install -r requirements.txt     # Python 3.11.5
```

## Architecture Overview

Multi-module Dash application for energy market analysis using EIA data. Five data modules feed into 50+ dashboard pages via a single-page app with manual URL routing.

### Entry Points

- **`app.py`** — Dash app initialization, loads initial WPS pivot data into `initial_data` dict. Exports `app` and `initial_data`.
- **`index.py`** — Main entry point. Imports all page modules (registering their callbacks), defines the sidebar navigation, URL routing (`display_page` callback), and sidebar collapse callbacks.

### Data Processing Modules

**WPS (Weekly Petroleum Status)** — `src/wps/`
- Downloads `psw09.xls` from EIA, parses all sheets, pivots by series ID
- `download_xlsx.py` → `generate_additional_tickers.py` → `generate_line_data.py` + `generate_seasonality_data.py`
- `mapping.py` contains the master `production_mapping` dict (EIA series ID → human name)
- `ag_mapping.py` defines AG Grid column configurations
- `table_mapping.py` defines table groupings used by page2_1 headline page

**STEO (Short-Term Energy Outlook)** — `src/steo/`
- Downloads monthly STEO Excel archives, tracks forecast evolution across release dates
- `chart_dpr.py` handles DPR (Drilling Productivity Report) chart generation with melted pivot data
- Metadata/mappings in `lookup/steo/` CSV files

**CLI (Company Level Imports)** — `src/cli/`
- `cli_data_processor.py` contains `CLIDataProcessor` class — loads parquet, categorizes by API gravity (Heavy/Medium/Light) and sulfur content (Sweet/Medium/Sour), converts monthly totals to kbd
- Data stored as zstd-compressed Parquet

**MSG** — `src/msg/`
- Parallel structure to WPS (same download/parse pattern) but for a separate data source
- Has its own `mapping.py`, `generate_line_data.py`, `generate_seasonality_data.py`

### WPS Page Pattern (page2_*.py)

Pages 2_2 through 2_9 follow a shared pattern using `src/wps/calculation.py`:

1. Define `idents` dict at top (EIA series IDs → display names for that commodity)
2. Define `graph_sections_input()` grouping graph IDs into named sections
3. Call `create_layout(page_id, commodity, graph_sections_input)` to generate the layout
4. Callbacks are created by `create_callbacks()` in `calculation.py`, which wires up:
   - Chart toggle (seasonality vs line view)
   - Year range toggles via `src/utils/variables.py` constants
   - Time range buttons (1m, 6m, 12m, 36m, all)
   - Graph rendering via `graph_line.py` (trend charts) and `graph_seag.py` (seasonality charts)

### URL Routing

Routes are defined in `index.py:display_page()` as a manual if/elif chain:
- `/home` → page1, `/stats/*` → page2_*, `/dpr/*` → page3_*
- `/steo/*` → page4_*, `/cli/*` → page5_*, `/psm/*` → page6_*

### Data Flow

1. `app.py` loads WPS pivot data into `initial_data` → stored in `dcc.Store(id='data-store', storage_type='session')`
2. page2_1 (Headline) has a "Generate and Save Data" button that triggers full WPS download + regeneration
3. Other pages load data directly via `src/utils/data_loader.py` → `simple_loader.py`

### Key Configuration

**`src/utils/variables.py`** — Year constants used across all WPS pages:
- `year_1_string`, `year_2_string`, `year_3_string` — the three comparison years
- `range_selector_normal` / `range_selector_last_five_years` — seasonality range keys
- `type_to_remove` — historical year types to filter out
- These need periodic manual updates as years roll forward

### Data Storage

- `data/wps/` — Feather files (`.feather`) for fast pandas loading
- `data/steo/` — Feather files for STEO pivot tables
- `data/cli/` — Parquet files (`.parquet`) with zstd compression
- `lookup/` — CSV reference data (STEO metadata, WPS mappings, release dates)

### Adding New Pages

1. Create `pages/pageN_X.py` following the naming convention
2. For WPS-style pages: define `idents` dict + `graph_sections_input()`, use `create_layout`/`create_callbacks`
3. Import in `index.py` with a descriptive comment
4. Add URL route in the `display_page()` callback chain
5. Add sidebar navigation entry in the appropriate `dbc.Collapse` section

### Adding New Data Sources

1. Create module in `src/` with download and processing scripts
2. Store processed data in `data/{module}/` as Feather or Parquet
3. Add loader methods to `SimpleDataLoader` in `src/utils/simple_loader.py`
4. Add update command to `main.py`
