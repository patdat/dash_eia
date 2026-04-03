# WPS PNG Report Generator — Design Spec

## Overview

A standalone Python script that reads processed WPS pipeline data and produces a single composite PNG image for sharing on Telegram. Provides a quick at-a-glance weekly petroleum status summary with tables and seasonality charts.

## Output

- **File**: `wps_export/output/wps_report.png`
- **Format**: Portrait, ~1200px wide, light theme (white background, dark text)
- **Target**: Telegram image sharing, readable on mobile

## Layout (top to bottom)

### 1. Header

"EIA Weekly Petroleum Status — Week Ending {date}" centered at the top. Date derived from the most recent observation in the dataset.

### 2. Tables Section

11 tables in a 2-column grid. Each table shows: series name, last 2 weeks' values, and week-over-week change (green positive, red negative).

| Row | Left | Right |
|-----|------|-------|
| 1 | Headline | Products Supplied |
| 2 | Crude Stocks | Crude Other Stocks |
| 3 | Crude Production | Crude Imports |
| 4 | Crude Adjustment | Crude Runs |
| 5 | Crude Exports | CDU Utilization |
| 6 | Feedstock Runs | _(empty)_ |

#### Table Definitions (series_id → display name)

**Headline:**
- `WCESTUS1` → US Commercial Stocks (kb)
- `W_EPC0_SAX_YCUOK_MBBL` → Cushing Stocks (kb)
- `WGTSTUS1` → US Gasoline Stocks (kb)
- `WDISTUS1` → US Distillate Stocks (kb)

**Products Supplied:**
- `WRPUPUS2` → Products (kbd)
- `WGFUPUS2` → Gasoline (kbd)
- `WDIUPUS2` → Distillate (kbd)
- `WKJUPUS2` → Jet (kbd)
- `WREUPUS2` → Fuel Oil (kbd)
- `WPRUP_NUS_2` → C3/C3= (kbd)
- `WWOUP_NUS_2` → Other Oils (kbd)

**Crude Stocks:**
- `WCESTUS1` → US Commercial Stocks (kb)
- `WCESTP11` → P1 Commercial Stocks (kb)
- `WCESTP21` → P2 Commercial Stocks (kb)
- `WCESTP31` → P3 Commercial Stocks (kb)
- `WCESTP41` → P4 Commercial Stocks (kb)
- `WCESTP51` → P5 Commercial Stocks (kb)

**Crude Other Stocks:**
- `W_EPC0_SAX_YCUOK_MBBL` → Cushing Stocks (kb)
- `crudeStocksP2E` → P2E Stocks (kb)
- `WCSSTUS1` → SPR Stocks (kb)
- `W_EPC0_SKA_NUS_MBBL` → Alaska Stocks (kb)
- `WCRSTUS1` → Total Stocks (kb)

**Crude Production:**
- `WCRFPUS2` → US Production (kbd)
- `W_EPC0_FPF_R48_MBBLD` → L48 Production (kbd)
- `W_EPC0_FPF_SAK_MBBLD` → AK Production (kbd)

**Crude Imports:**
- `WCEIMUS2` → US Imports (kbd)
- `WCEIMP12` → P1 Imports (kbd)
- `WCEIMP22` → P2 Imports (kbd)
- `WCEIMP32` → P3 Imports (kbd)
- `WCEIMP42` → P4 Imports (kbd)
- `WCEIMP52` → P5 Imports (kbd)

**Crude Adjustment:**
- `crudeOriginalAdjustment` → OG Adjustment Factor (kbd)

**Crude Runs:**
- `WCRRIUS2` → US Refinery Runs (kbd)
- `WCRRIP12` → P1 Refinery Runs (kbd)
- `WCRRIP22` → P2 Refinery Runs (kbd)
- `WCRRIP32` → P3 Refinery Runs (kbd)
- `WCRRIP42` → P4 Refinery Runs (kbd)
- `WCRRIP52` → P5 Refinery Runs (kbd)

**Crude Exports:**
- `WCREXUS2` → US Crude Exports (kbd)

**CDU Utilization:**
- `WPULEUS3` → US Refinery Utilization (pct)
- `W_NA_YUP_R10_PER` → P1 Refinery Utilization (pct)
- `W_NA_YUP_R20_PER` → P2 Refinery Utilization (pct)
- `W_NA_YUP_R30_PER` → P3 Refinery Utilization (pct)
- `W_NA_YUP_R40_PER` → P4 Refinery Utilization (pct)
- `W_NA_YUP_R50_PER` → P5 Refinery Utilization (pct)

**Feedstock Runs:**
- `feedstockRunsUS` → US Feedstock Runs (kbd)
- `feddStockRunsP1` → P1 Feedstock Runs (kbd)
- `feedstockRunsP2` → P2 Feedstock Runs (kbd)
- `feedstockRunsP3` → P3 Feedstock Runs (kbd)
- `feedstockRunsP4` → P4 Feedstock Runs (kbd)
- `feedstockRunsP5` → P5 Feedstock Runs (kbd)

### 3. Charts Section

4 seasonality charts in a 2x2 grid:

| | Left | Right |
|---|------|-------|
| Top | US Commercial Crude Stocks (`WCESTUS1`) | Cushing Crude Stocks (`W_EPC0_SAX_YCUOK_MBBL`) |
| Bottom | US Gasoline Stocks (`WGTSTUS1`) | US Distillate Stocks (`WDISTUS1`) |

#### Seasonality Chart Spec

Each chart renders:
- **Range band**: gray filled area between min and max values across a historical range (2015–2023)
- **Average line**: black dotted line through the historical average
- **Year lines**: 5 colored lines for current year (2026) + 4 prior years (2025, 2024, 2023, 2022)
- **X-axis**: Jan through Dec, with month labels at ~4-week intervals (week positions 0, 5, 9, 14, 18, 22, 27, 31, 36, 40, 45, 49)
- **Y-axis**: auto-scaled per chart
- **Title**: series display name above each chart

#### Seasonality Data Computation

From the weekly parquet (`data/eia/ingestion/wps.parquet`):
1. Filter to the target `series_id`
2. Parse date, derive `year` and `week_of_year` (ISO week or sequential week, matching existing dashboard behavior)
3. For the range band: filter years 2015–2023, group by `week_of_year`, compute `min`, `max`, `mean`
4. For year lines: filter each year (2022–2026), extract `week_of_year` vs `value`

## Implementation

### File Structure

```
wps_export/
  scripts/
    generate_report.py    # <-- new file (single script, self-contained)
  output/                 # <-- new directory (created at runtime)
    wps_report.png
```

### Script Structure

```python
# generate_report.py

# 1. TABLE_DEFS: dict of {table_name: {series_id: display_name}}
# 2. CHART_SERIES: list of series IDs for the 4 seasonality charts
# 3. load_data(): reads wps.parquet, returns DataFrame
# 4. build_table_data(df): extracts last 2 weeks, computes change, returns per-table DataFrames
# 5. compute_seasonality(df, series_id): computes range band + year lines for one series
# 6. render_table(ax, table_name, table_df): renders one table into a matplotlib Axes
# 7. render_seasonality_chart(ax, series_id, seasonality_data): renders one chart into an Axes
# 8. generate_report(): orchestrates everything, saves PNG
# 9. if __name__ == "__main__": generate_report()
```

### matplotlib Layout

- `Figure` with `GridSpec` for precise layout control
- Top region: 6 rows x 2 columns for tables (using `ax.table()` or manual text rendering)
- Bottom region: 2 rows x 2 columns for charts
- `fig.savefig()` with `dpi=150` for crisp Telegram rendering at ~1200px width

### Dependencies

Add `matplotlib>=3.7.0` to `wps_export/requirements.txt`. All other deps (pandas, pyarrow) already present.

### Usage

```bash
cd wps_export
python scripts/generate_report.py
# Produces: output/wps_report.png
```

### Color Scheme

- **Background**: white
- **Text**: black / dark gray
- **Table headers**: light gray background (#e0e0e0), bold
- **Change column**: green (#4caf50) for positive, red (#ef5350) for negative
- **Range band**: light gray fill (#e0e0e0)
- **Average line**: black dotted
- **Year line colors**: match existing dashboard YEAR_COLORS pattern (distinct, colorblind-friendly)

## What This Does NOT Include

- No Telegram bot / sending logic — generates the file only
- No pipeline integration — fully standalone, run manually
- No Dash app dependency — self-contained data loading and table definitions
- No interactive charts — pure static PNG
