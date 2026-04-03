# WPS PNG Report Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone script that reads WPS pipeline parquet data and produces a single composite PNG with summary tables and 4 seasonality charts, suitable for Telegram sharing.

**Architecture:** Single-file matplotlib script (`wps_export/scripts/generate_report.py`) that loads `wps_export/data/eia/ingestion/wps.parquet`, computes week-over-week table data and seasonality band/year data, then renders everything into one portrait-oriented figure via GridSpec.

**Tech Stack:** Python, pandas, matplotlib

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `wps_export/scripts/generate_report.py` | Create | All report logic: data loading, table definitions, seasonality computation, rendering, PNG export |
| `wps_export/tests/test_generate_report.py` | Create | Unit tests for data functions (build_table_data, compute_seasonality) |
| `wps_export/requirements.txt` | Modify | Add `matplotlib>=3.7.0` |

---

### Task 1: Add matplotlib dependency

**Files:**
- Modify: `wps_export/requirements.txt`

- [ ] **Step 1: Add matplotlib to requirements.txt**

Add this line to `wps_export/requirements.txt`:

```
matplotlib>=3.7.0
```

- [ ] **Step 2: Install and verify**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
pip install matplotlib>=3.7.0
python -c "import matplotlib; print(matplotlib.__version__)"
```
Expected: prints a version >= 3.7.0

- [ ] **Step 3: Commit**

```bash
git add wps_export/requirements.txt
git commit -m "feat(wps-report): add matplotlib dependency"
```

---

### Task 2: Data loading and table data computation

**Files:**
- Create: `wps_export/scripts/generate_report.py` (partial — data layer only)
- Create: `wps_export/tests/test_generate_report.py`

- [ ] **Step 1: Write failing tests for load_data and build_table_data**

Create `wps_export/tests/test_generate_report.py`:

```python
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from scripts.generate_report import (
    TABLE_DEFS,
    CHART_SERIES,
    load_data,
    build_table_data,
)


class TestTableDefs:
    """Verify table definitions are complete and consistent."""

    def test_table_defs_has_11_tables(self):
        assert len(TABLE_DEFS) == 11

    def test_headline_series_ids(self):
        assert "WCESTUS1" in TABLE_DEFS["Headline"]
        assert "W_EPC0_SAX_YCUOK_MBBL" in TABLE_DEFS["Headline"]
        assert "WGTSTUS1" in TABLE_DEFS["Headline"]
        assert "WDISTUS1" in TABLE_DEFS["Headline"]

    def test_chart_series_has_4_ids(self):
        assert len(CHART_SERIES) == 4
        assert "WCESTUS1" in CHART_SERIES
        assert "W_EPC0_SAX_YCUOK_MBBL" in CHART_SERIES


class TestBuildTableData:
    """Test week-over-week table computation."""

    @pytest.fixture
    def sample_df(self):
        """Minimal WPS-shaped DataFrame with 3 weeks of data for 2 series."""
        rows = []
        dates = pd.to_datetime(["2026-03-14", "2026-03-21", "2026-03-28"])
        for d in dates:
            rows.append({"date": d, "series_id": "WCESTUS1", "value": 430.0 + (d.day - 14)})
            rows.append({"date": d, "series_id": "WGTSTUS1", "value": 230.0 + (d.day - 14)})
        return pd.DataFrame(rows)

    def test_returns_dict_keyed_by_table_name(self, sample_df):
        result = build_table_data(sample_df)
        assert isinstance(result, dict)
        # Should have entries for tables whose series are present
        assert "Headline" in result

    def test_table_has_correct_columns(self, sample_df):
        result = build_table_data(sample_df)
        headline = result["Headline"]
        assert "name" in headline.columns
        assert "change" in headline.columns
        # Should have the two most recent date columns
        assert len(headline.columns) == 4  # name, week1, week2, change

    def test_change_is_week_over_week(self, sample_df):
        result = build_table_data(sample_df)
        headline = result["Headline"]
        row = headline[headline["name"] == "US Commercial Stocks (kb)"]
        assert len(row) == 1
        # week2 value - week1 value
        change = row["change"].iloc[0]
        assert change == pytest.approx(7.0)  # (28-14) - (21-14) = 14 - 7 = 7

    def test_missing_series_excluded(self, sample_df):
        result = build_table_data(sample_df)
        # CDU Utilization series aren't in sample data
        if "CDU Utilization" in result:
            assert result["CDU Utilization"].empty

    def test_week_ending_date(self, sample_df):
        result = build_table_data(sample_df)
        headline = result["Headline"]
        # The two date columns should be the last 2 unique dates
        date_cols = [c for c in headline.columns if c not in ("name", "change")]
        assert len(date_cols) == 2
        assert date_cols[1] == "03/28"  # Most recent
        assert date_cols[0] == "03/21"  # Prior week
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python -m pytest tests/test_generate_report.py -v
```
Expected: FAIL — `scripts.generate_report` does not exist yet

- [ ] **Step 3: Implement data layer in generate_report.py**

Create `wps_export/scripts/generate_report.py`:

```python
#!/usr/bin/env python3
"""
WPS PNG Report Generator

Reads WPS pipeline parquet data and produces a single composite PNG with
summary tables and seasonality charts. Designed for Telegram sharing.

Usage:
    cd wps_export
    python scripts/generate_report.py
"""

import os
import sys

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INPUT_PARQUET = "./data/eia/ingestion/wps.parquet"
OUTPUT_DIR = "./output"
OUTPUT_PNG = os.path.join(OUTPUT_DIR, "wps_report.png")

# Table definitions: {table_name: {series_id: display_name}}
TABLE_DEFS = {
    "Headline": {
        "WCESTUS1": "US Commercial Stocks (kb)",
        "W_EPC0_SAX_YCUOK_MBBL": "Cushing Stocks (kb)",
        "WGTSTUS1": "US Gasoline Stocks (kb)",
        "WDISTUS1": "US Distillate Stocks (kb)",
    },
    "Products Supplied": {
        "WRPUPUS2": "Products (kbd)",
        "WGFUPUS2": "Gasoline (kbd)",
        "WDIUPUS2": "Distillate (kbd)",
        "WKJUPUS2": "Jet (kbd)",
        "WREUPUS2": "Fuel Oil (kbd)",
        "WPRUP_NUS_2": "C3/C3= (kbd)",
        "WWOUP_NUS_2": "Other Oils (kbd)",
    },
    "Crude Stocks": {
        "WCESTUS1": "US Commercial Stocks (kb)",
        "WCESTP11": "P1 Commercial Stocks (kb)",
        "WCESTP21": "P2 Commercial Stocks (kb)",
        "WCESTP31": "P3 Commercial Stocks (kb)",
        "WCESTP41": "P4 Commercial Stocks (kb)",
        "WCESTP51": "P5 Commercial Stocks (kb)",
    },
    "Crude Other Stocks": {
        "W_EPC0_SAX_YCUOK_MBBL": "Cushing Stocks (kb)",
        "crudeStocksP2E": "P2E Stocks (kb)",
        "WCSSTUS1": "SPR Stocks (kb)",
        "W_EPC0_SKA_NUS_MBBL": "Alaska Stocks (kb)",
        "WCRSTUS1": "Total Stocks (kb)",
    },
    "Crude Production": {
        "WCRFPUS2": "US Production (kbd)",
        "W_EPC0_FPF_R48_MBBLD": "L48 Production (kbd)",
        "W_EPC0_FPF_SAK_MBBLD": "AK Production (kbd)",
    },
    "Crude Imports": {
        "WCEIMUS2": "US Imports (kbd)",
        "WCEIMP12": "P1 Imports (kbd)",
        "WCEIMP22": "P2 Imports (kbd)",
        "WCEIMP32": "P3 Imports (kbd)",
        "WCEIMP42": "P4 Imports (kbd)",
        "WCEIMP52": "P5 Imports (kbd)",
    },
    "Crude Adjustment": {
        "crudeOriginalAdjustment": "OG Adjustment Factor (kbd)",
    },
    "Crude Runs": {
        "WCRRIUS2": "US Refinery Runs (kbd)",
        "WCRRIP12": "P1 Refinery Runs (kbd)",
        "WCRRIP22": "P2 Refinery Runs (kbd)",
        "WCRRIP32": "P3 Refinery Runs (kbd)",
        "WCRRIP42": "P4 Refinery Runs (kbd)",
        "WCRRIP52": "P5 Refinery Runs (kbd)",
    },
    "Crude Exports": {
        "WCREXUS2": "US Crude Exports (kbd)",
    },
    "CDU Utilization": {
        "WPULEUS3": "US Refinery Utilization (pct)",
        "W_NA_YUP_R10_PER": "P1 Refinery Utilization (pct)",
        "W_NA_YUP_R20_PER": "P2 Refinery Utilization (pct)",
        "W_NA_YUP_R30_PER": "P3 Refinery Utilization (pct)",
        "W_NA_YUP_R40_PER": "P4 Refinery Utilization (pct)",
        "W_NA_YUP_R50_PER": "P5 Refinery Utilization (pct)",
    },
    "Feedstock Runs": {
        "feedstockRunsUS": "US Feedstock Runs (kbd)",
        "feddStockRunsP1": "P1 Feedstock Runs (kbd)",
        "feedstockRunsP2": "P2 Feedstock Runs (kbd)",
        "feedstockRunsP3": "P3 Feedstock Runs (kbd)",
        "feedstockRunsP4": "P4 Feedstock Runs (kbd)",
        "feedstockRunsP5": "P5 Feedstock Runs (kbd)",
    },
}

# 2x2 grid order for the table layout
TABLE_GRID = [
    ("Headline", "Products Supplied"),
    ("Crude Stocks", "Crude Other Stocks"),
    ("Crude Production", "Crude Imports"),
    ("Crude Adjustment", "Crude Runs"),
    ("Crude Exports", "CDU Utilization"),
    ("Feedstock Runs", None),
]

# Series IDs for the 4 seasonality charts
CHART_SERIES = [
    "WCESTUS1",
    "W_EPC0_SAX_YCUOK_MBBL",
    "WGTSTUS1",
    "WDISTUS1",
]

CHART_NAMES = {
    "WCESTUS1": "US Commercial Crude Stocks (mb)",
    "W_EPC0_SAX_YCUOK_MBBL": "Cushing Crude Stocks (mb)",
    "WGTSTUS1": "US Gasoline Stocks (mb)",
    "WDISTUS1": "US Distillate Stocks (mb)",
}

# Seasonality config
RANGE_BAND_YEARS = list(range(2015, 2024))  # 2015-2023 for min/max/avg
CURRENT_YEAR = 2026
DISPLAY_YEARS = [2026, 2025, 2024, 2023, 2022]

# Colors (matching existing dashboard)
YEAR_COLORS = ["#000000", "#00ADEF", "#EC002B", "#4AB04D", "#F68E2F"]
POSITIVE_COLOR = "#4caf50"
NEGATIVE_COLOR = "#ef5350"
HEADER_BG = "#e0e0e0"
RANGE_BAND_COLOR = "#e8e8e8"

# Seasonality x-axis
TICK_POSITIONS = [0, 5, 9, 14, 18, 22, 27, 31, 36, 40, 45, 49]
TICK_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(parquet_path=INPUT_PARQUET):
    """Load WPS parquet and return DataFrame with date as datetime."""
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------------------------
# Table data
# ---------------------------------------------------------------------------
def build_table_data(df):
    """Build per-table DataFrames with last 2 weeks and week-over-week change.

    Returns:
        dict of {table_name: DataFrame} with columns [name, week1_date, week2_date, change]
    """
    all_series_ids = set()
    for idents in TABLE_DEFS.values():
        all_series_ids.update(idents.keys())

    # Filter to relevant series
    subset = df[df["series_id"].isin(all_series_ids)].copy()

    # Get last 2 unique dates
    unique_dates = sorted(subset["date"].unique())
    if len(unique_dates) < 2:
        raise ValueError(f"Need at least 2 dates, found {len(unique_dates)}")
    last_two = unique_dates[-2:]

    # Pivot: rows=series_id, columns=date, values=value
    recent = subset[subset["date"].isin(last_two)]
    pivot = recent.pivot_table(index="series_id", columns="date", values="value")

    # Format date column names as MM/DD
    date_labels = {d: pd.Timestamp(d).strftime("%m/%d") for d in last_two}
    pivot = pivot.rename(columns=date_labels)

    col1 = date_labels[last_two[0]]
    col2 = date_labels[last_two[1]]

    result = {}
    for table_name, idents in TABLE_DEFS.items():
        rows = []
        for sid, display_name in idents.items():
            if sid in pivot.index:
                v1 = pivot.loc[sid, col1] if col1 in pivot.columns else np.nan
                v2 = pivot.loc[sid, col2] if col2 in pivot.columns else np.nan
                change = v2 - v1 if pd.notna(v1) and pd.notna(v2) else np.nan
            else:
                v1, v2, change = np.nan, np.nan, np.nan
            rows.append({"name": display_name, col1: v1, col2: v2, "change": change})

        result[table_name] = pd.DataFrame(rows)

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python -m pytest tests/test_generate_report.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add wps_export/scripts/generate_report.py wps_export/tests/test_generate_report.py
git commit -m "feat(wps-report): add data loading and table computation"
```

---

### Task 3: Seasonality computation

**Files:**
- Modify: `wps_export/scripts/generate_report.py`
- Modify: `wps_export/tests/test_generate_report.py`

- [ ] **Step 1: Write failing tests for compute_seasonality**

Append to `wps_export/tests/test_generate_report.py`:

```python
from scripts.generate_report import compute_seasonality


class TestComputeSeasonality:
    """Test seasonality band and year line computation."""

    @pytest.fixture
    def seasonality_df(self):
        """DataFrame with weekly data for WCESTUS1 across multiple years."""
        rows = []
        # Generate 52 weeks for years 2015-2026
        for year in range(2015, 2027):
            base = 400 + (year - 2015) * 5  # slowly increasing baseline
            for week in range(52):
                date = pd.Timestamp(f"{year}-01-01") + pd.Timedelta(weeks=week)
                # Sinusoidal seasonal pattern
                value = base + 20 * np.sin(2 * np.pi * week / 52)
                rows.append({
                    "date": date,
                    "series_id": "WCESTUS1",
                    "value": value,
                })
        return pd.DataFrame(rows)

    def test_returns_dict_with_required_keys(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        assert "week_of_year" in result
        assert "min" in result
        assert "max" in result
        assert "mean" in result
        assert "years" in result

    def test_range_band_computed_from_historical_years(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        # min should be less than or equal to max at every point
        for i in range(len(result["min"])):
            assert result["min"][i] <= result["max"][i]

    def test_year_lines_has_display_years(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        year_keys = list(result["years"].keys())
        assert 2026 in year_keys
        assert 2025 in year_keys
        assert 2024 in year_keys

    def test_week_of_year_is_sequential(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        weeks = result["week_of_year"]
        assert weeks[0] == 0
        assert weeks[-1] <= 52
        assert all(weeks[i] <= weeks[i + 1] for i in range(len(weeks) - 1))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python -m pytest tests/test_generate_report.py::TestComputeSeasonality -v
```
Expected: FAIL — `compute_seasonality` not defined

- [ ] **Step 3: Implement compute_seasonality**

Add to `wps_export/scripts/generate_report.py` after `build_table_data`:

```python
# ---------------------------------------------------------------------------
# Seasonality computation
# ---------------------------------------------------------------------------
def compute_seasonality(df, series_id):
    """Compute seasonality data for one series.

    Returns dict with:
        week_of_year: list of ints (0-52)
        min: list of floats (range band lower)
        max: list of floats (range band upper)
        mean: list of floats (average line)
        years: dict of {year: list of (week, value) tuples}
    """
    series = df[df["series_id"] == series_id].copy()
    series["year"] = series["date"].dt.year
    # Use ISO week but 0-indexed to match existing dashboard
    series["week_of_year"] = series["date"].dt.isocalendar().week.astype(int) - 1

    # Range band from historical years (2015-2023)
    historical = series[series["year"].isin(RANGE_BAND_YEARS)]
    band = historical.groupby("week_of_year")["value"].agg(["min", "max", "mean"])
    band = band.sort_index()

    weeks = band.index.tolist()

    # Year lines for display years
    years_data = {}
    for year in DISPLAY_YEARS:
        year_data = series[series["year"] == year].sort_values("week_of_year")
        if not year_data.empty:
            years_data[year] = list(
                zip(year_data["week_of_year"].tolist(), year_data["value"].tolist())
            )

    return {
        "week_of_year": weeks,
        "min": band["min"].tolist(),
        "max": band["max"].tolist(),
        "mean": band["mean"].tolist(),
        "years": years_data,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python -m pytest tests/test_generate_report.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add wps_export/scripts/generate_report.py wps_export/tests/test_generate_report.py
git commit -m "feat(wps-report): add seasonality computation"
```

---

### Task 4: Table rendering

**Files:**
- Modify: `wps_export/scripts/generate_report.py`

- [ ] **Step 1: Implement render_table function**

Add to `wps_export/scripts/generate_report.py` after `compute_seasonality`. This renders a single table into a matplotlib Axes using `ax.table()`:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------
def render_table(ax, table_name, table_df):
    """Render a summary table into a matplotlib Axes.

    Args:
        ax: matplotlib Axes to draw into
        table_name: string title above the table
        table_df: DataFrame with columns [name, date1, date2, change]
    """
    ax.axis("off")

    if table_df.empty or table_df.dropna(subset=["change"]).empty:
        ax.text(0.5, 0.5, f"{table_name}\n(no data)", ha="center", va="center",
                fontsize=9, color="#999999", transform=ax.transAxes)
        return

    # Format numeric values for display
    display_data = []
    date_cols = [c for c in table_df.columns if c not in ("name", "change")]
    for _, row in table_df.iterrows():
        fmt_row = [row["name"]]
        for dc in date_cols:
            val = row[dc]
            if pd.notna(val):
                fmt_row.append(f"{val:,.1f}" if abs(val) < 1000 else f"{val:,.0f}")
            else:
                fmt_row.append("—")
        chg = row["change"]
        if pd.notna(chg):
            sign = "+" if chg > 0 else ""
            fmt_row.append(f"{sign}{chg:,.1f}" if abs(chg) < 100 else f"{sign}{chg:,.0f}")
        else:
            fmt_row.append("—")
        display_data.append(fmt_row)

    col_labels = [""] + date_cols + ["Chg"]

    tbl = ax.table(
        cellText=display_data,
        colLabels=col_labels,
        cellLoc="right",
        loc="upper center",
        colWidths=[0.45] + [0.18] * (len(date_cols) + 1),
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7)
    tbl.scale(1, 1.2)

    # Style header row
    for j in range(len(col_labels)):
        cell = tbl[0, j]
        cell.set_facecolor(HEADER_BG)
        cell.set_text_props(fontweight="bold", fontsize=7)
        cell.set_edgecolor("#cccccc")

    # Style name column left-aligned, color the change column
    for i in range(len(display_data)):
        # Name cell: left-aligned
        tbl[i + 1, 0].set_text_props(ha="left", fontsize=7)
        tbl[i + 1, 0].set_edgecolor("#cccccc")

        # Date value cells
        for j in range(1, len(date_cols) + 1):
            tbl[i + 1, j].set_edgecolor("#cccccc")

        # Change cell: colored
        chg_cell = tbl[i + 1, len(col_labels) - 1]
        chg_cell.set_edgecolor("#cccccc")
        chg_val = table_df.iloc[i]["change"]
        if pd.notna(chg_val):
            if chg_val > 0:
                chg_cell.set_text_props(color=POSITIVE_COLOR, fontweight="bold")
            elif chg_val < 0:
                chg_cell.set_text_props(color=NEGATIVE_COLOR, fontweight="bold")

    # Table title
    ax.set_title(table_name, fontsize=8, fontweight="bold", loc="left", pad=2)
```

- [ ] **Step 2: Smoke-test table rendering with a quick visual check**

Add a temporary test at the bottom of the script (we'll replace it in Task 6):

```python
if __name__ == "__main__":
    # Quick smoke test — render one table
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = load_data()
    tables = build_table_data(df)
    fig, ax = plt.subplots(figsize=(5, 3))
    render_table(ax, "Headline", tables["Headline"])
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig.savefig(os.path.join(OUTPUT_DIR, "test_table.png"), dpi=150, bbox_inches="tight")
    print(f"Saved test table to {OUTPUT_DIR}/test_table.png")
```

- [ ] **Step 3: Run the smoke test (only if data exists)**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python scripts/generate_report.py
```
Expected: If `data/eia/ingestion/wps.parquet` exists, creates `output/test_table.png`. If not, a `FileNotFoundError` is expected — that's fine, we'll test with real data later.

- [ ] **Step 4: Commit**

```bash
git add wps_export/scripts/generate_report.py
git commit -m "feat(wps-report): add table rendering"
```

---

### Task 5: Seasonality chart rendering

**Files:**
- Modify: `wps_export/scripts/generate_report.py`

- [ ] **Step 1: Implement render_seasonality_chart**

Add to `wps_export/scripts/generate_report.py` after `render_table`:

```python
# ---------------------------------------------------------------------------
# Seasonality chart rendering
# ---------------------------------------------------------------------------
def render_seasonality_chart(ax, series_id, seasonality_data):
    """Render a seasonality chart into a matplotlib Axes.

    Args:
        ax: matplotlib Axes
        series_id: EIA series ID (for title lookup)
        seasonality_data: dict from compute_seasonality()
    """
    weeks = seasonality_data["week_of_year"]
    band_min = seasonality_data["min"]
    band_max = seasonality_data["max"]
    band_mean = seasonality_data["mean"]
    years_data = seasonality_data["years"]

    # Range band
    ax.fill_between(weeks, band_min, band_max, color=RANGE_BAND_COLOR, zorder=1)

    # Average line
    ax.plot(weeks, band_mean, color="#000000", linestyle=":", linewidth=0.8, zorder=2)

    # Year lines
    for i, year in enumerate(DISPLAY_YEARS):
        if year in years_data:
            pts = years_data[year]
            w = [p[0] for p in pts]
            v = [p[1] for p in pts]
            color = YEAR_COLORS[i] if i < len(YEAR_COLORS) else "#888888"
            linewidth = 1.8 if year == CURRENT_YEAR else 1.2
            ax.plot(w, v, color=color, linewidth=linewidth, label=str(year), zorder=3 + i)

    # X-axis: month labels
    ax.set_xticks(TICK_POSITIONS)
    ax.set_xticklabels(TICK_LABELS, fontsize=6)
    ax.set_xlim(0, 52)

    # Y-axis
    ax.tick_params(axis="y", labelsize=6)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # Grid and spines
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    # Title
    title = CHART_NAMES.get(series_id, series_id)
    ax.set_title(title, fontsize=8, fontweight="bold", loc="left", pad=4)

    # Legend
    ax.legend(fontsize=5, loc="upper right", framealpha=0.8, ncol=2)
```

- [ ] **Step 2: Commit**

```bash
git add wps_export/scripts/generate_report.py
git commit -m "feat(wps-report): add seasonality chart rendering"
```

---

### Task 6: Full report assembly and main entry point

**Files:**
- Modify: `wps_export/scripts/generate_report.py`

- [ ] **Step 1: Implement generate_report and replace __main__ block**

Replace the temporary `if __name__` block and add the `generate_report` function at the end of `wps_export/scripts/generate_report.py`:

```python
# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def generate_report(parquet_path=INPUT_PARQUET, output_path=OUTPUT_PNG):
    """Generate the full composite PNG report.

    Args:
        parquet_path: path to wps.parquet
        output_path: path for output PNG
    """
    print("Loading data...")
    df = load_data(parquet_path)

    # Determine week-ending date from most recent data point
    max_date = df["date"].max()
    week_ending = max_date.strftime("%B %d, %Y")

    print(f"Week ending: {week_ending}")
    print("Building table data...")
    tables = build_table_data(df)

    print("Computing seasonality...")
    seasonality = {}
    for sid in CHART_SERIES:
        seasonality[sid] = compute_seasonality(df, sid)

    # --- Build the figure ---
    # Layout: header + 6 table rows (2 cols each) + 2 chart rows (2 cols each)
    # Total rows: 1 (header) + 6 (tables) + 2 (charts) = 9
    fig = plt.figure(figsize=(8, 18), facecolor="white")
    gs = GridSpec(
        nrows=9, ncols=2, figure=fig,
        hspace=0.35, wspace=0.15,
        top=0.97, bottom=0.02, left=0.03, right=0.97,
        height_ratios=[0.3, 1, 1, 1, 1, 1, 0.7, 1.5, 1.5],
    )

    # Header
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.axis("off")
    ax_header.text(
        0.5, 0.5,
        f"EIA Weekly Petroleum Status \u2014 Week Ending {week_ending}",
        ha="center", va="center", fontsize=12, fontweight="bold",
        transform=ax_header.transAxes,
    )

    # Tables (rows 1-6, 2 columns)
    for row_idx, (left_name, right_name) in enumerate(TABLE_GRID):
        # Left table
        ax_left = fig.add_subplot(gs[row_idx + 1, 0])
        if left_name and left_name in tables:
            render_table(ax_left, left_name, tables[left_name])
        else:
            ax_left.axis("off")

        # Right table
        ax_right = fig.add_subplot(gs[row_idx + 1, 1])
        if right_name and right_name in tables:
            render_table(ax_right, right_name, tables[right_name])
        else:
            ax_right.axis("off")

    # Charts (rows 7-8, 2 columns — mapped to gs rows 7 and 8)
    chart_positions = [(7, 0), (7, 1), (8, 0), (8, 1)]
    for i, (row, col) in enumerate(chart_positions):
        ax_chart = fig.add_subplot(gs[row, col])
        sid = CHART_SERIES[i]
        render_seasonality_chart(ax_chart, sid, seasonality[sid])

    # Save
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    generate_report()
```

- [ ] **Step 2: Move matplotlib imports to top of file**

Ensure these imports are at the top of the file (below pandas/numpy), replacing any inline imports from Task 4:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
```

Remove any duplicate `import matplotlib` / `import matplotlib.pyplot as plt` lines from inside `render_table` or the old `__main__` block.

- [ ] **Step 3: Run the full report (if data exists)**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python scripts/generate_report.py
```
Expected: If parquet exists, creates `output/wps_report.png`. Open and visually verify layout.

- [ ] **Step 4: Run all tests**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python -m pytest tests/test_generate_report.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add wps_export/scripts/generate_report.py
git commit -m "feat(wps-report): add full report assembly and main entry point"
```

---

### Task 7: Visual polish and end-to-end test

**Files:**
- Modify: `wps_export/scripts/generate_report.py` (tuning only)

- [ ] **Step 1: Run the pipeline to get fresh data (if not already available)**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python main.py --force
```
Expected: Downloads EIA data, creates `data/eia/ingestion/wps.parquet`

- [ ] **Step 2: Generate the report**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python scripts/generate_report.py
```
Expected: Creates `output/wps_report.png`

- [ ] **Step 3: Visual review**

Open `output/wps_report.png` and verify:
- Header shows correct week-ending date
- All 11 tables render with data (no "no data" placeholders for series that exist in the parquet)
- Change column is green for positive, red for negative
- 4 seasonality charts show range bands, average lines, and colored year lines
- Charts have month labels on x-axis and a legend
- Text is readable at phone-screen zoom levels
- Overall layout is balanced — no overlapping elements

- [ ] **Step 4: Tune spacing if needed**

Common adjustments:
- `height_ratios` in GridSpec — change if tables or charts need more/less vertical space
- `figsize` — increase height if tables overlap
- `tbl.set_fontsize()` — increase if text is too small for mobile
- `hspace` / `wspace` — adjust gaps between subplots

- [ ] **Step 5: Run all tests one final time**

Run:
```bash
cd /Users/patrickmarable/Documents/GitHub/dash_eia/wps_export
python -m pytest tests/ -v
```
Expected: All tests PASS (both existing test_wps.py and new test_generate_report.py)

- [ ] **Step 6: Commit**

```bash
git add wps_export/scripts/generate_report.py
git commit -m "feat(wps-report): visual polish and spacing tuning"
```

---

### Task 8: Add output directory to .gitignore

**Files:**
- Modify or create: `wps_export/.gitignore`

- [ ] **Step 1: Add output/ to gitignore**

Append to `wps_export/.gitignore` (create if it doesn't exist):

```
output/
```

- [ ] **Step 2: Also add .superpowers/ to project root .gitignore if not already there**

Check and append to `/Users/patrickmarable/Documents/GitHub/dash_eia/.gitignore`:

```
.superpowers/
```

- [ ] **Step 3: Commit**

```bash
git add wps_export/.gitignore .gitignore
git commit -m "chore: add output/ and .superpowers/ to gitignore"
```
