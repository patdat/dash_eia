# EIA Energy Dashboard

A comprehensive energy data analytics dashboard for tracking petroleum markets, drilling productivity, and energy forecasts using EIA (Energy Information Administration) data.

## Overview

This dashboard provides real-time analysis of energy markets by processing multiple EIA data sources into an interactive, multi-page Dash application. It serves traders, analysts, and researchers with fundamental market intelligence through 50+ specialized analysis pages.

## Features

### 📊 Market Analysis Modules

- **Weekly Petroleum Status (WPS)** - Real-time tracking of US petroleum stocks, production, imports, and refinery operations
- **Drilling Productivity Reports (DPR)** - Regional shale production analysis across major basins
- **Short-Term Energy Outlook (STEO)** - EIA forecast data with historical evolution tracking
- **Company Level Imports (CLI)** - Detailed crude oil import analysis by company and country of origin

### 🎯 Key Capabilities

- **Real-time Energy Analytics** - Track crude oil, gasoline, distillate, jet fuel, and other petroleum products
- **Regional Analysis** - Monitor production across Bakken, Eagle Ford, Haynesville, Permian, and other key regions
- **Quality Arbitrage Analysis** - Track API gravity and sulfur content for trading opportunities
- **PADD Regional Analytics** - Supply/demand imbalances across US petroleum districts
- **Interactive Visualizations** - Dynamic charts with customizable time series analysis
- **Advanced Caching System** - Multi-level caching for instant data access

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python index.py

# Dashboard will be available at http://localhost:8050
```

## Data Management

### Full Data Refresh
```bash
# Update all data sources
python main.py
```

### Module-Specific Updates
```bash
# Weekly petroleum data
python -m src.wps.download_xlsx

# STEO forecast data
python -m src.steo.download

# Company-level import data
python -m src.cli.main

# Drilling productivity data
python -m src.cli.download
```

### Data Storage Structure
```
data/
├── wps/                    # Weekly petroleum data
│   ├── wps_gte_2015.feather
│   ├── graph_line_data.feather
│   └── seasonality_data.feather
├── steo/                   # Forecast data
│   ├── steo_pivot.feather
│   └── steo_pivot_dpr.feather
├── cli/                    # Import data
│   └── companylevelimports_crude.parquet
└── lookup/                 # Reference data
```

## Project Structure

```
dash_eia/
├── index.py               # Main application entry point
├── app.py                 # Dash app initialization
├── main.py                # Data update orchestrator
├── pages/                 # Dashboard pages
│   ├── page1.py          # Home dashboard
│   ├── page2_*.py        # WPS analysis (15 pages)
│   ├── page3_*.py        # DPR analysis (10 pages)
│   ├── page4_*.py        # STEO analysis (6 pages)
│   ├── page5_*.py        # CLI analysis (10 pages)
│   └── page6_*.py        # Future modules
├── src/                   # Core processing modules
│   ├── wps/              # Weekly petroleum processing
│   ├── steo/             # Forecast data processing
│   ├── cli/              # Import data processing
│   └── utils/            # Shared utilities & caching
├── data/                  # Processed data storage
└── lookup/                # Reference tables
```

## Advanced Features

### Performance Optimization
- **Feather Format** - Ultra-fast DataFrame serialization
- **Parquet Compression** - Efficient storage for large datasets
- **LRU Memory Cache** - In-memory caching with TTL
- **Smart File Cache** - Automatic invalidation on data updates
- **Preload System** - Common datasets loaded at startup

### Trading & Analysis Tools
- **Supply Disruption Detection** - Automated alerts for import anomalies
- **Crack Spread Calculator** - Refinery margin analysis
- **Quality Arbitrage Signals** - Heavy/sour vs light/sweet spreads
- **Seasonal Pattern Analysis** - Monthly trading opportunities
- **Market Concentration Tracker** - Company dependency analysis

### Data Processing Pipeline
1. **Download** - Automated fetching from EIA sources
2. **Transform** - Data cleaning and standardization
3. **Enrich** - Calculated fields and derived metrics
4. **Store** - Optimized file formats for fast access
5. **Cache** - Multi-level caching for performance


## Development

### Adding New Pages
1. Create page file in `pages/` following naming convention
2. Import in `index.py` with descriptive comment
3. Add navigation entry in sidebar
4. Use `src/utils/data_loader.py` for cached data access

### Adding Data Sources
1. Create module in `src/` with download scripts
2. Process to Feather/Parquet format
3. Add update command to `main.py`
4. Update this README with new commands

## Requirements

### Core Dependencies
- Python 3.8+
- Dash 2.0+
- Pandas 1.5+
- Plotly 5.0+
- Dash Bootstrap Components
- Dash AG Grid

### Data Processing
- PyArrow (Feather format)
- Requests (API calls)
- NumPy (calculations)

See `requirements.txt` for complete list.

## Performance Tips

- Keep browser cache enabled for static assets
- Use AG Grid for tables with >100 rows
- Preload cache on startup in production
- Update data during off-peak hours
- Monitor `app.log` for performance metrics

## Troubleshooting

### Common Issues

**Slow Initial Load**
- Run `python -c "from src.utils.data_loader import preload_common_data; preload_common_data()"`

**Missing Data**
- Run `python main.py` for full refresh

**Cache Issues**
- Cache is managed automatically on data updates

## Contributing

1. Follow existing code patterns and naming conventions
2. Update CLAUDE.md for architectural changes
3. Test with multiple data update cycles
4. Ensure callbacks are efficient

## License

MIT