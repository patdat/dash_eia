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
import datetime as _dt

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INPUT_PARQUET = "./data/eia/ingestion/wps.parquet"
MONTHLY_PARQUET = "./data/eia/processed/wps_monthly.parquet"
OUTPUT_DIR = "./output"
OUTPUT_PNG = os.path.join(OUTPUT_DIR, "wps_report.png")

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
    "Gross Runs": {
        "WGIRIUS2": "US Gross Runs (kbd)",
        "WGIRIP12": "P1 Gross Runs (kbd)",
        "WGIRIP22": "P2 Gross Runs (kbd)",
        "WGIRIP32": "P3 Gross Runs (kbd)",
        "WGIRIP42": "P4 Gross Runs (kbd)",
        "WGIRIP52": "P5 Gross Runs (kbd)",
    },
    "Gasoline Stocks": {
        "WGTSTUS1": "US Gasoline Stocks (kb)",
        "WGTSTP11": "P1 Gasoline Stocks (kb)",
        "WGTSTP21": "P2 Gasoline Stocks (kb)",
        "WGTSTP31": "P3 Gasoline Stocks (kb)",
        "WGTSTP41": "P4 Gasoline Stocks (kb)",
        "WGTSTP51": "P5 Gasoline Stocks (kb)",
    },
    "Distillate Stocks": {
        "WDISTUS1": "US Distillate Stocks (kb)",
        "WDISTP11": "P1 Distillate Stocks (kb)",
        "WDISTP21": "P2 Distillate Stocks (kb)",
        "WDISTP31": "P3 Distillate Stocks (kb)",
        "WDISTP41": "P4 Distillate Stocks (kb)",
        "WDISTP51": "P5 Distillate Stocks (kb)",
    },
    "Jet Stocks": {
        "WKJSTUS1": "US Jet Stocks (kb)",
        "WKJSTP11": "P1 Jet Stocks (kb)",
        "WKJSTP21": "P2 Jet Stocks (kb)",
        "WKJSTP31": "P3 Jet Stocks (kb)",
        "WKJSTP41": "P4 Jet Stocks (kb)",
        "WKJSTP51": "P5 Jet Stocks (kb)",
    },
    "Fuel Oil Stocks": {
        "WRESTUS1": "US Fuel Oil Stocks (kb)",
        "WRESTP11": "P1 Fuel Oil Stocks (kb)",
        "WRESTP21": "P2 Fuel Oil Stocks (kb)",
        "WRESTP31": "P3 Fuel Oil Stocks (kb)",
        "WRESTP41": "P4 Fuel Oil Stocks (kb)",
        "WRESTP51": "P5 Fuel Oil Stocks (kb)",
    },
    "Propane Stocks": {
        "WPRSTUS1": "US C3/C3= Stocks (kb)",
        "WPRSTP11": "P1 C3/C3= Stocks (kb)",
        "WPRSTP21": "P2 C3/C3= Stocks (kb)",
        "WPRSTP31": "P3 C3/C3= Stocks (kb)",
        "WPRST_R4N5_1": "P4P5 C3/C3= Stocks (kb)",
    },
}

# 3-column layout: each column is a list of table names, stacked top to bottom.
# Heights are proportional to the number of data rows in each table.
TABLE_COLUMNS = [
    # Column 1: Headline + Refining
    [
        "Headline",
        "Products Supplied",
        "CDU Utilization",
        "Feedstock Runs",
        "Gross Runs",
    ],
    # Column 2: Crude
    [
        "Crude Stocks",
        "Crude Other Stocks",
        "Crude Production",
        "Crude Imports",
        "Crude Exports",
        "Crude Runs",
        "Crude Adjustment",
    ],
    # Column 3: Product Stocks
    [
        "Gasoline Stocks",
        "Distillate Stocks",
        "Jet Stocks",
        "Fuel Oil Stocks",
        "Propane Stocks",
    ],
]

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

_current_year = _dt.date.today().year
CURRENT_YEAR = _current_year
DISPLAY_YEARS = [_current_year - i for i in range(5)]
RANGE_BAND_YEARS = list(range(2015, _current_year - 2))  # up to 3 years before current

YEAR_COLORS = ["#000000", "#00ADEF", "#EC002B", "#4AB04D", "#F68E2F"]
POSITIVE_COLOR = "#4caf50"
NEGATIVE_COLOR = "#ef5350"
HEADER_BG = "#e0e0e0"
RANGE_BAND_COLOR = "#e8e8e8"

TICK_POSITIONS = [0, 5, 9, 14, 18, 22, 27, 31, 36, 40, 45, 49]
TICK_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data(parquet_path=INPUT_PARQUET):
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------------------------
# Derived series computation
# ---------------------------------------------------------------------------
# These series don't exist in the raw EIA parquet — they're computed from
# raw series, matching the logic in src/wps/generate_additional_tickers.py.

DERIVED_SERIES = {
    # Feedstock Runs = Gross Runs - Crude Runs
    "feedstockRunsUS":  ("WGIRIUS2",  "WCRRIUS2"),
    "feddStockRunsP1":  ("WGIRIP12",  "WCRRIP12"),
    "feedstockRunsP2":  ("WGIRIP22",  "WCRRIP22"),
    "feedstockRunsP3":  ("WGIRIP32",  "WCRRIP32"),
    "feedstockRunsP4":  ("WGIRIP42",  "WCRRIP42"),
    "feedstockRunsP5":  ("WGIRIP52",  "WCRRIP52"),
    # P2E Stocks = P2 Stocks - Cushing Stocks
    "crudeStocksP2E":   ("WCESTP21",  "W_EPC0_SAX_YCUOK_MBBL"),
}


def compute_derived_series(df):
    """Compute derived series from raw EIA data and append to the DataFrame.

    Handles:
    - Feedstock Runs (Gross Runs minus Crude Runs) for US and PADDs 1-5
    - P2E Stocks (P2 minus Cushing)
    - Crude Adjustment Factor (balance sheet residual)
    """
    # Pivot to wide format for arithmetic
    pivot = df.pivot_table(index="date", columns="series_id", values="value")

    new_rows = []

    # Simple subtraction series (feedstock runs + P2E stocks)
    for derived_id, (series_a, series_b) in DERIVED_SERIES.items():
        if series_a in pivot.columns and series_b in pivot.columns:
            result = pivot[series_a] - pivot[series_b]
            for date, value in result.dropna().items():
                new_rows.append({"date": date, "series_id": derived_id, "value": value})

    # Crude Adjustment Factor: -(Production + Imports - Runs - Exports - StockChange)
    adj_cols = ["WCRFPUS2", "WCEIMUS2", "WCRRIUS2", "WCREXUS2", "WCRSTUS1"]
    if all(c in pivot.columns for c in adj_cols):
        stock_change = pivot["WCRSTUS1"].diff() / 7
        adjustment = -(
            pivot["WCRFPUS2"] + pivot["WCEIMUS2"]
            - pivot["WCRRIUS2"] - pivot["WCREXUS2"]
            - stock_change
        )
        for date, value in adjustment.dropna().items():
            new_rows.append({"date": date, "series_id": "crudeOriginalAdjustment", "value": value})

    if new_rows:
        derived_df = pd.DataFrame(new_rows)
        derived_df["date"] = pd.to_datetime(derived_df["date"])
        return pd.concat([df, derived_df], ignore_index=True)

    return df


def build_table_data(df, monthly_df=None):
    """Build per-table DataFrames with latest value, w/w, monthly value, and m/m.

    Returns:
        (date_label, month_label, dict of {table_name: DataFrame})
    """
    all_series_ids = set()
    for idents in TABLE_DEFS.values():
        all_series_ids.update(idents.keys())

    subset = df[df["series_id"].isin(all_series_ids)].copy()

    # Get last 2 weekly dates for w/w
    unique_dates = sorted(subset["date"].unique())
    if len(unique_dates) < 2:
        raise ValueError(f"Need at least 2 dates, found {len(unique_dates)}")
    last_two = unique_dates[-2:]
    date_label = pd.Timestamp(last_two[-1]).strftime("%m/%d")

    recent = subset[subset["date"].isin(last_two)]
    pivot = recent.pivot_table(index="series_id", columns="date", values="value")

    # Monthly: last 2 months for m/m, current month value for display
    monthly_pivot = None
    month_label = ""
    if monthly_df is not None and not monthly_df.empty:
        monthly_df = monthly_df.copy()
        monthly_df["date"] = pd.to_datetime(monthly_df["date"])
        monthly_df["raw_id"] = monthly_df["series_id"].str.replace("_plm", "", case=False, regex=False)
        monthly_dates = sorted(monthly_df["date"].unique())
        if len(monthly_dates) >= 2:
            last_two_months = monthly_dates[-2:]
            # Format as "Mar-26" style
            month_label = pd.Timestamp(last_two_months[-1]).strftime("%b-%y").lower()
            m_recent = monthly_df[monthly_df["date"].isin(last_two_months)]
            monthly_pivot = m_recent.pivot_table(index="raw_id", columns="date", values="value")

    result = {}
    for table_name, idents in TABLE_DEFS.items():
        rows = []
        for sid, display_name in idents.items():
            # Latest weekly value
            val = np.nan
            if sid in pivot.index and last_two[-1] in pivot.columns:
                val = pivot.loc[sid, last_two[-1]]

            # w/w change
            wow = np.nan
            if sid in pivot.index and len(pivot.columns) == 2:
                v_prev = pivot.loc[sid, last_two[0]] if last_two[0] in pivot.columns else np.nan
                v_curr = pivot.loc[sid, last_two[-1]] if last_two[-1] in pivot.columns else np.nan
                if pd.notna(v_prev) and pd.notna(v_curr):
                    wow = v_curr - v_prev

            # Monthly value + m/m change
            m_val = np.nan
            mom = np.nan
            m_key = None
            if monthly_pivot is not None:
                if sid in monthly_pivot.index:
                    m_key = sid
                elif sid.upper() in monthly_pivot.index:
                    m_key = sid.upper()
            if m_key is not None:
                m_cols = monthly_pivot.columns
                if len(m_cols) >= 2:
                    m_prev = monthly_pivot.loc[m_key, m_cols[-2]]
                    m_curr = monthly_pivot.loc[m_key, m_cols[-1]]
                    m_val = m_curr
                    if pd.notna(m_prev) and pd.notna(m_curr):
                        mom = m_curr - m_prev

            rows.append({
                "name": display_name,
                date_label: val,
                "w/w": wow,
                month_label: m_val,
                "m/m": mom,
            })
        result[table_name] = pd.DataFrame(rows)

    return date_label, month_label, result


def compute_seasonality(df, series_id):
    series = df[df["series_id"] == series_id].copy()
    series["year"] = series["date"].dt.year
    series["week_of_year"] = series["date"].dt.isocalendar().week.astype(int).clip(upper=52) - 1

    historical = series[series["year"].isin(RANGE_BAND_YEARS)]
    band = historical.groupby("week_of_year")["value"].agg(["min", "max", "mean"])
    band = band.sort_index()

    weeks = band.index.tolist()

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


def _fmt_value(val, is_pct=False):
    """Format a numeric value for display. Pct gets 1 decimal, all else 0."""
    if pd.isna(val):
        return "\u2014"
    if is_pct:
        return f"{val:,.1f}"
    return f"{val:,.0f}"


def _fmt_change(val, is_pct=False):
    """Format a change value with +/- sign."""
    if pd.isna(val):
        return "\u2014"
    sign = "+" if val > 0 else ""
    if is_pct:
        return f"{sign}{val:,.1f}"
    return f"{sign}{val:,.0f}"


def render_table(ax, table_name, table_df):
    ax.axis("off")

    if table_df.empty:
        ax.text(0.5, 0.5, f"{table_name}\n(no data)", ha="center", va="center",
                fontsize=9, color="#999999", transform=ax.transAxes)
        return

    # Columns: name, weekly_value, w/w, monthly_value, m/m
    non_special = [c for c in table_df.columns if c not in ("name", "w/w", "m/m")]
    date_col = non_special[0]   # weekly date
    month_col = non_special[1] if len(non_special) > 1 else None  # monthly date

    display_data = []
    for _, row in table_df.iterrows():
        is_pct = "pct" in str(row["name"]).lower()
        fmt_row = [
            row["name"],
            _fmt_value(row[date_col], is_pct),
            _fmt_change(row["w/w"], is_pct),
        ]
        if month_col:
            fmt_row.append(_fmt_value(row[month_col], is_pct))
            fmt_row.append(_fmt_change(row["m/m"], is_pct))
        display_data.append(fmt_row)

    if month_col:
        col_labels = ["", date_col, "w/w", month_col, "m/m"]
        col_widths = [0.38, 0.155, 0.155, 0.155, 0.155]
    else:
        col_labels = ["", date_col, "w/w"]
        col_widths = [0.40, 0.30, 0.30]

    tbl = ax.table(
        cellText=display_data,
        colLabels=col_labels,
        cellLoc="right",
        loc="upper center",
        colWidths=col_widths,
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7)
    tbl.scale(1, 1.2)

    # Style header row — monthly columns get darker background
    monthly_col_indices = set()
    if month_col:
        for j, label in enumerate(col_labels):
            if label in (month_col, "m/m"):
                monthly_col_indices.add(j)

    for j in range(len(col_labels)):
        cell = tbl[0, j]
        is_monthly = j in monthly_col_indices
        cell.set_facecolor("#555555" if is_monthly else HEADER_BG)
        cell.set_edgecolor("#cccccc")
        if j == 0:
            cell.set_text_props(fontweight="bold", fontsize=7)
        elif is_monthly:
            cell.set_text_props(fontweight="bold", fontsize=7, ha="right", color="white")
        else:
            cell.set_text_props(fontweight="bold", fontsize=7, ha="right")

    # Style data rows
    for i in range(len(display_data)):
        tbl[i + 1, 0].set_text_props(ha="left", fontsize=7)
        tbl[i + 1, 0].set_edgecolor("#cccccc")

        for j in range(1, len(col_labels)):
            tbl[i + 1, j].set_edgecolor("#cccccc")

        # Color w/w column (index 2)
        wow_val = table_df.iloc[i]["w/w"]
        if pd.notna(wow_val) and wow_val != 0:
            color = POSITIVE_COLOR if wow_val > 0 else NEGATIVE_COLOR
            tbl[i + 1, 2].set_text_props(color=color, fontweight="bold")

        # Color m/m column (index 4, skip monthly value at index 3)
        if month_col and "m/m" in table_df.columns:
            mom_val = table_df.iloc[i]["m/m"]
            if pd.notna(mom_val) and mom_val != 0:
                color = POSITIVE_COLOR if mom_val > 0 else NEGATIVE_COLOR
                tbl[i + 1, 4].set_text_props(color=color, fontweight="bold")

    ax.set_title(table_name, fontsize=8, fontweight="bold", loc="left", pad=2)


def render_seasonality_chart(ax, series_id, seasonality_data):
    weeks = seasonality_data["week_of_year"]
    band_min = seasonality_data["min"]
    band_max = seasonality_data["max"]
    band_mean = seasonality_data["mean"]
    years_data = seasonality_data["years"]

    ax.fill_between(weeks, band_min, band_max, color=RANGE_BAND_COLOR, zorder=1)
    ax.plot(weeks, band_mean, color="#000000", linestyle=":", linewidth=0.8, zorder=2)

    for i, year in enumerate(DISPLAY_YEARS):
        if year in years_data:
            pts = years_data[year]
            w = [p[0] for p in pts]
            v = [p[1] for p in pts]
            color = YEAR_COLORS[i] if i < len(YEAR_COLORS) else "#888888"
            linewidth = 1.8 if year == CURRENT_YEAR else 1.2
            ax.plot(w, v, color=color, linewidth=linewidth, label=str(year), zorder=3 + i)

    ax.set_xticks(TICK_POSITIONS)
    ax.set_xticklabels(TICK_LABELS, fontsize=6)
    ax.set_xlim(0, 52)

    ax.tick_params(axis="y", labelsize=6)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    title = CHART_NAMES.get(series_id, series_id)
    ax.set_title(title, fontsize=8, fontweight="bold", loc="left", pad=4)

    ax.legend(fontsize=5, loc="upper right", framealpha=0.8, ncol=2)


def _table_row_count(table_name):
    """Number of data rows + 1 header row."""
    return len(TABLE_DEFS.get(table_name, {})) + 1


# Layout constants (in inches)
ROW_HEIGHT = 0.215       # height per table row (header or data), accounts for scale(1, 1.2)
TABLE_GAP = 0.18         # vertical gap between tables (title space)
COL_MARGIN = 0.03        # horizontal gap between columns
HEADER_HEIGHT = 0.4      # report title height
CHART_HEIGHT = 2.5       # per chart row height
FIG_WIDTH = 14


def generate_report(parquet_path=INPUT_PARQUET, output_path=OUTPUT_PNG):
    print("Loading data...")
    df = load_data(parquet_path)

    print("Computing derived series...")
    df = compute_derived_series(df)

    max_date = df["date"].max()
    week_ending = max_date.strftime("%B %d, %Y")

    # Load monthly data for m/m changes
    monthly_df = None
    if os.path.exists(MONTHLY_PARQUET):
        monthly_df = pd.read_parquet(MONTHLY_PARQUET)
        print(f"Loaded monthly data: {len(monthly_df)} rows")

    print(f"Week ending: {week_ending}")
    print("Building table data...")
    date_label, month_label, tables = build_table_data(df, monthly_df)

    print("Computing seasonality...")
    seasonality = {}
    for sid in CHART_SERIES:
        seasonality[sid] = compute_seasonality(df, sid)

    # --- Compute figure height from content ---
    num_cols = len(TABLE_COLUMNS)
    col_heights_in = []
    for col_tables in TABLE_COLUMNS:
        h = 0
        for i, t in enumerate(col_tables):
            h += _table_row_count(t) * ROW_HEIGHT
            if i < len(col_tables) - 1:
                h += TABLE_GAP
        col_heights_in.append(h)

    table_section_height = max(col_heights_in)
    chart_section_height = CHART_HEIGHT * 2 + 0.4  # 2 rows of charts + gap
    fig_height = HEADER_HEIGHT + table_section_height + chart_section_height + 0.3

    fig = plt.figure(figsize=(FIG_WIDTH, fig_height), facecolor="white")

    # --- Header (in figure coordinates: 0=bottom, 1=top) ---
    header_top = 1.0
    header_bottom = 1.0 - HEADER_HEIGHT / fig_height
    ax_header = fig.add_axes([0, header_bottom, 1, HEADER_HEIGHT / fig_height])
    ax_header.axis("off")
    ax_header.text(
        0.5, 0.5,
        f"EIA Weekly Petroleum Status \u2014 Week Ending {week_ending}",
        ha="center", va="center", fontsize=14, fontweight="bold",
        transform=ax_header.transAxes,
    )

    # --- Tables: manually position each axes ---
    table_top = header_bottom - 0.01  # start just below header
    col_width = (1.0 - COL_MARGIN * (num_cols + 1)) / num_cols

    for col_idx, col_tables in enumerate(TABLE_COLUMNS):
        left = COL_MARGIN + col_idx * (col_width + COL_MARGIN)
        cursor_y = table_top  # tracks current y position (top-down)

        for table_name in col_tables:
            num_rows = _table_row_count(table_name)
            ax_height = num_rows * ROW_HEIGHT / fig_height
            bottom = cursor_y - ax_height

            ax = fig.add_axes([left, bottom, col_width, ax_height])
            if table_name in tables:
                render_table(ax, table_name, tables[table_name])
            else:
                ax.axis("off")

            cursor_y = bottom - TABLE_GAP / fig_height

    # --- Charts: 2x2 grid below tables ---
    assert len(CHART_SERIES) == 4, "Update chart layout if CHART_SERIES changes"
    chart_top = table_top - table_section_height / fig_height - 0.02
    chart_w = (1.0 - COL_MARGIN * 3) / 2
    chart_h = CHART_HEIGHT / fig_height
    chart_gap_h = 0.4 / fig_height  # vertical gap between chart rows
    chart_gap_w = COL_MARGIN

    chart_positions = [
        (COL_MARGIN, chart_top - chart_h),                              # top-left
        (COL_MARGIN + chart_w + chart_gap_w, chart_top - chart_h),      # top-right
        (COL_MARGIN, chart_top - chart_h * 2 - chart_gap_h),            # bottom-left
        (COL_MARGIN + chart_w + chart_gap_w, chart_top - chart_h * 2 - chart_gap_h),  # bottom-right
    ]
    for i, (cx, cy) in enumerate(chart_positions):
        ax_chart = fig.add_axes([cx, cy, chart_w, chart_h])
        render_seasonality_chart(ax_chart, CHART_SERIES[i], seasonality[CHART_SERIES[i]])

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    generate_report()
