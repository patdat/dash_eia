import pandas as pd
import numpy as np
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go
from src.utils.data_loader import loader
from src.utils.colors import (
    RED, BLUE, GREEN, ORANGE, PURPLE, BLACK,
    POSITIVE, NEGATIVE,
    GRAY_50, GRAY_200, GRAY_300, GRAY_500, GRAY_800,
)
from src.utils.variables import years_last_five_years_range

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_STYLE = {"padding": "2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"}

CHART_HEIGHT = 480

CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
    height=CHART_HEIGHT,
    margin=dict(l=60, r=20, t=50, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    font=dict(family="Montserrat"),
    xaxis=dict(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300),
    yaxis=dict(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300),
)

# Series IDs used across the page
SERIES = {
    # Crude balance
    "crude_prod": "WCRFPUS2",
    "crude_prod_l48": "W_EPC0_FPF_R48_MBBLD",
    "crude_prod_ak": "W_EPC0_FPF_SAK_MBBLD",
    "crude_imp": "WCEIMUS2",
    "crude_imp_p1": "WCEIMP12",
    "crude_imp_p2": "WCEIMP22",
    "crude_imp_p3": "WCEIMP32",
    "crude_imp_p4": "WCEIMP42",
    "crude_imp_p5": "WCEIMP52",
    "crude_exp": "WCREXUS2",
    "crude_adj": "crudeOriginalAdjustment",
    "crude_runs": "WCRRIUS2",
    "crude_runs_p1": "WCRRIP12",
    "crude_runs_p2": "WCRRIP22",
    "crude_runs_p3": "WCRRIP32",
    "crude_runs_p4": "WCRRIP42",
    "crude_runs_p5": "WCRRIP52",
    "crude_stocks": "WCESTUS1",
    # Products supplied (demand proxy)
    "ps_total": "WRPUPUS2",
    "ps_gasoline": "WGFUPUS2",
    "ps_distillate": "WDIUPUS2",
    "ps_jet": "WKJUPUS2",
    "ps_fueloil": "WREUPUS2",
    "ps_c3": "WPRUP_NUS_2",
    "ps_other": "WWOUP_NUS_2",
    # Refinery
    "ref_util": "WPULEUS3",
    # Product stocks
    "gas_stocks": "WGTSTUS1",
    "dist_stocks": "WDISTUS1",
    "jet_stocks": "WKJSTUS1",
    # Product trade
    "gas_prod": "WGFRPUS2",
    "gas_imp": "WGTIMUS2",
    "gas_exp": "W_EPM0F_EEX_NUS-Z00_MBBLD",
    "dist_prod": "WDIRPUS2",
    "dist_imp": "WDIIMUS2",
    "dist_exp": "WDIEXUS2",
    "jet_prod": "WKJRPUS2",
    "jet_imp": "WKJIMUS2",
    "jet_exp": "WKJEXUS2",
}

# Product selector configuration
PRODUCT_CONFIG = {
    "crude": {
        "label": "Crude Oil",
        "stock": "crude_stocks",
        "demand": "crude_runs",
        "prod": "crude_prod",
        "imp": "crude_imp",
        "exp": "crude_exp",
        "stock_uom": "kb",
        "demand_label": "Refinery Inputs",
    },
    "gasoline": {
        "label": "Gasoline",
        "stock": "gas_stocks",
        "demand": "ps_gasoline",
        "prod": "gas_prod",
        "imp": "gas_imp",
        "exp": "gas_exp",
        "stock_uom": "kb",
        "demand_label": "Products Supplied",
    },
    "distillate": {
        "label": "Distillate",
        "stock": "dist_stocks",
        "demand": "ps_distillate",
        "prod": "dist_prod",
        "imp": "dist_imp",
        "exp": "dist_exp",
        "stock_uom": "kb",
        "demand_label": "Products Supplied",
    },
    "jet": {
        "label": "Jet Fuel",
        "stock": "jet_stocks",
        "demand": "ps_jet",
        "prod": "jet_prod",
        "imp": "jet_imp",
        "exp": "jet_exp",
        "stock_uom": "kb",
        "demand_label": "Products Supplied",
    },
}

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _safe_get(row, series_key):
    """Get a value from a row using SERIES mapping, return NaN if missing."""
    sid = SERIES.get(series_key, series_key)
    try:
        v = row[sid]
        return float(v) if pd.notna(v) else np.nan
    except (KeyError, TypeError):
        return np.nan


def _load_pivot():
    """Load and sort WPS pivot data."""
    df = loader.load_wps_pivot_data()
    df = df.sort_values("period").reset_index(drop=True)
    return df


def _find_year_ago(df, target_period):
    """Find the row closest to one year before target_period."""
    target = target_period - pd.Timedelta(days=364)
    idx = (df["period"] - target).abs().idxmin()
    return df.loc[idx]


def _five_year_avg(df, target_week, col):
    """Compute 5-year average for a column at a given ISO week."""
    mask = (df["period"].dt.isocalendar().week.astype(int) == target_week) & (
        df["period"].dt.year.isin(years_last_five_years_range)
    )
    subset = df.loc[mask, col]
    return subset.mean() if len(subset) > 0 else np.nan


def _five_year_stats(df, col):
    """Return a DataFrame with week -> (mean, min, max) for 5-year range."""
    mask = df["period"].dt.year.isin(years_last_five_years_range)
    sub = df.loc[mask].copy()
    sub["week"] = sub["period"].dt.isocalendar().week.astype(int)
    if col not in sub.columns:
        return pd.DataFrame(columns=["week", "mean", "min", "max"])
    grouped = sub.groupby("week")[col].agg(["mean", "min", "max"]).reset_index()
    return grouped


def build_balance_data():
    """Build all data needed for the page: KPIs, balance table, chart data."""
    df = _load_pivot()
    if df.empty:
        return None

    latest = df.iloc[-1]
    prior = df.iloc[-2] if len(df) >= 2 else latest
    yago = _find_year_ago(df, latest["period"])
    latest_week = int(latest["period"].isocalendar().week)

    latest_date = latest["period"]
    prior_date = prior["period"]
    yago_date = yago["period"]

    # --- Build balance table rows ---
    def _row(item, indent=0, series_key=None, uom="kbd", is_header=False, computed_vals=None, five_yr_override=None):
        if is_header and computed_vals is None:
            return {
                "item": item, "indent": indent,
                "latest": None, "prior": None, "wow": None,
                "year_ago": None, "yoy": None, "five_yr": None, "vs_5yr": None,
                "uom": "", "is_header": True,
            }
        if computed_vals:
            lv, pv, yv = computed_vals
        else:
            lv = _safe_get(latest, series_key)
            pv = _safe_get(prior, series_key)
            yv = _safe_get(yago, series_key)

        if five_yr_override is not None:
            fv = five_yr_override
        elif series_key:
            sid_for_avg = SERIES.get(series_key, series_key)
            fv = _five_year_avg(df, latest_week, sid_for_avg)
        else:
            fv = np.nan

        wow = lv - pv if pd.notna(lv) and pd.notna(pv) else np.nan
        yoy = lv - yv if pd.notna(lv) and pd.notna(yv) else np.nan
        vs5 = lv - fv if pd.notna(lv) and pd.notna(fv) else np.nan

        return {
            "item": item, "indent": indent,
            "latest": lv, "prior": pv, "wow": wow,
            "year_ago": yv, "yoy": yoy, "five_yr": fv, "vs_5yr": vs5,
            "uom": uom, "is_header": is_header,
        }

    # --- Computed items ---
    # Supply = Production + Imports + Adjustment
    def _sum_safe(*vals):
        clean = [v for v in vals if pd.notna(v)]
        return sum(clean) if clean else np.nan

    supply_l = _sum_safe(_safe_get(latest, "crude_prod"), _safe_get(latest, "crude_imp"), _safe_get(latest, "crude_adj"))
    supply_p = _sum_safe(_safe_get(prior, "crude_prod"), _safe_get(prior, "crude_imp"), _safe_get(prior, "crude_adj"))
    supply_y = _sum_safe(_safe_get(yago, "crude_prod"), _safe_get(yago, "crude_imp"), _safe_get(yago, "crude_adj"))

    # Demand = Refinery Runs + Crude Exports
    demand_l = _sum_safe(_safe_get(latest, "crude_runs"), _safe_get(latest, "crude_exp"))
    demand_p = _sum_safe(_safe_get(prior, "crude_runs"), _safe_get(prior, "crude_exp"))
    demand_y = _sum_safe(_safe_get(yago, "crude_runs"), _safe_get(yago, "crude_exp"))

    # Balance = Supply - Demand
    balance_l = supply_l - demand_l if pd.notna(supply_l) and pd.notna(demand_l) else np.nan
    balance_p = supply_p - demand_p if pd.notna(supply_p) and pd.notna(demand_p) else np.nan
    balance_y = supply_y - demand_y if pd.notna(supply_y) and pd.notna(demand_y) else np.nan

    # 5-yr averages for computed rows
    _5yr = lambda key: _five_year_avg(df, latest_week, SERIES[key])
    supply_5yr = _sum_safe(_5yr("crude_prod"), _5yr("crude_imp"), _5yr("crude_adj"))
    demand_5yr = _sum_safe(_5yr("crude_runs"), _5yr("crude_exp"))
    balance_5yr = supply_5yr - demand_5yr if pd.notna(supply_5yr) and pd.notna(demand_5yr) else np.nan
    stk_chg_5yr = round(balance_5yr / 7000, 1) if pd.notna(balance_5yr) else np.nan
    stk_5yr = round(_5yr("crude_stocks") / 1000, 1) if pd.notna(_5yr("crude_stocks")) else np.nan

    # Stock change = balance (kbd) / 7000 → mb, rounded to 1 decimal
    def _to_mb_balance(v):
        return round(v / 7000, 1) if pd.notna(v) else np.nan

    stk_chg_l = _to_mb_balance(balance_l)
    stk_chg_p = _to_mb_balance(balance_p)
    stk_chg_y = _to_mb_balance(balance_y)

    # Stocks in mb (kb ÷ 1000), rounded to 1 decimal
    def _to_mb_stocks(v):
        return round(v / 1000, 1) if pd.notna(v) else np.nan

    stk_l = _to_mb_stocks(_safe_get(latest, "crude_stocks"))
    stk_p = _to_mb_stocks(_safe_get(prior, "crude_stocks"))
    stk_y = _to_mb_stocks(_safe_get(yago, "crude_stocks"))

    rows = [
        # SUPPLY (parent with total)
        _row("SUPPLY", 0, is_header=True, computed_vals=(supply_l, supply_p, supply_y), five_yr_override=supply_5yr),
        _row("Production", 1, series_key="crude_prod"),
        _row("L48", 2, series_key="crude_prod_l48"),
        _row("Alaska", 2, series_key="crude_prod_ak"),
        _row("Imports", 1, series_key="crude_imp"),
        _row("P1", 2, series_key="crude_imp_p1"),
        _row("P2", 2, series_key="crude_imp_p2"),
        _row("P3", 2, series_key="crude_imp_p3"),
        _row("P4", 2, series_key="crude_imp_p4"),
        _row("P5", 2, series_key="crude_imp_p5"),
        _row("Adjustment", 1, series_key="crude_adj"),
        # DEMAND (parent with total)
        _row("DEMAND", 0, is_header=True, computed_vals=(demand_l, demand_p, demand_y), five_yr_override=demand_5yr),
        _row("Refinery Inputs", 1, series_key="crude_runs"),
        _row("P1", 2, series_key="crude_runs_p1"),
        _row("P2", 2, series_key="crude_runs_p2"),
        _row("P3", 2, series_key="crude_runs_p3"),
        _row("P4", 2, series_key="crude_runs_p4"),
        _row("P5", 2, series_key="crude_runs_p5"),
        _row("Exports", 1, series_key="crude_exp"),
        # BALANCE (parent with total)
        _row("BALANCE", 0, is_header=True, computed_vals=(balance_l, balance_p, balance_y), five_yr_override=balance_5yr),
        _row("Stock Change (mb)", 1, uom="mb", computed_vals=(stk_chg_l, stk_chg_p, stk_chg_y), five_yr_override=stk_chg_5yr),
        _row("Crude Stocks (mb)", 1, uom="mb", computed_vals=(stk_l, stk_p, stk_y), five_yr_override=stk_5yr),
        # PRODUCTS SUPPLIED
        _row("PRODUCTS SUPPLIED", 0, is_header=True),
        _row("Total", 1, series_key="ps_total"),
        _row("Gasoline", 1, series_key="ps_gasoline"),
        _row("Distillate", 1, series_key="ps_distillate"),
        _row("Jet Fuel", 1, series_key="ps_jet"),
        _row("Fuel Oil", 1, series_key="ps_fueloil"),
        _row("C3/C3=", 1, series_key="ps_c3"),
        _row("Other Oils", 1, series_key="ps_other"),
    ]

    return {
        "rows": rows,
        "latest_date": latest_date.strftime("%m/%d"),
        "prior_date": prior_date.strftime("%m/%d"),
        "yago_date": yago_date.strftime("%m/%d/%y"),
        "pivot_json": df.to_json(date_format="iso", orient="split"),
    }


# ---------------------------------------------------------------------------
# KPI metric cards (same pattern as page1.py)
# ---------------------------------------------------------------------------

def _fmt(value, unit, divisor=1):
    if pd.isna(value):
        return "—"
    v = value / divisor
    if unit == "%":
        return f"{v:.1f}%"
    elif unit == "kbd":
        return f"{v:,.0f} kbd"
    else:
        return f"{v:.1f} mb"


def _fmt_change(change, unit, divisor=1):
    if pd.isna(change):
        return "—"
    v = change / divisor
    sign = "+" if v >= 0 else ""
    if unit == "%":
        return f"{sign}{v:.1f}%"
    elif unit == "kbd":
        return f"{sign}{v:,.0f} kbd"
    else:
        return f"{sign}{v:.1f} mb"


def _metric_card(title, value_str, change_str, change_positive, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, style={
                "fontSize": "0.75rem", "fontWeight": "700",
                "letterSpacing": "0.08em", "color": GRAY_500,
                "marginBottom": "0.35rem",
            }),
            html.Div(value_str, style={
                "fontSize": "1.5rem", "fontWeight": "700",
                "color": GRAY_800, "marginBottom": "0.25rem",
            }),
            html.Span(change_str, style={
                "fontSize": "0.85rem", "fontWeight": "600",
                "color": POSITIVE if change_positive else NEGATIVE,
            }),
            html.Span(" w/w", style={
                "fontSize": "0.8rem", "color": GRAY_500, "marginLeft": "3px",
            }),
        ], style={"padding": "1rem 1.25rem"}),
        style={
            "borderLeft": f"3px solid {color}",
            "borderRadius": "4px",
            "backgroundColor": "white",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
            "border": f"1px solid {GRAY_200}",
            "borderLeftWidth": "3px",
            "borderLeftColor": color,
        },
    )


def _build_kpi_strip():
    try:
        df = _load_pivot()
        latest = df.iloc[-1]
        prior = df.iloc[-2]
    except Exception:
        return dbc.Row(html.Div("Unable to load metrics.", style={"color": GRAY_500}))

    prod_l = _safe_get(latest, "crude_prod")
    prod_p = _safe_get(prior, "crude_prod")
    net_l = _safe_get(latest, "crude_imp") - _safe_get(latest, "crude_exp")
    net_p = _safe_get(prior, "crude_imp") - _safe_get(prior, "crude_exp")
    util_l = _safe_get(latest, "ref_util")
    util_p = _safe_get(prior, "ref_util")
    stk_l = _safe_get(latest, "crude_stocks")
    stk_p = _safe_get(prior, "crude_stocks")
    stk_chg = stk_l - stk_p
    stk_chg_prior = stk_p - _safe_get(df.iloc[-3], "crude_stocks") if len(df) >= 3 else np.nan
    ps_l = _safe_get(latest, "ps_total")
    ps_p = _safe_get(prior, "ps_total")

    cards_data = [
        ("CRUDE PRODUCTION", prod_l, prod_l - prod_p, "kbd", 1, GREEN),
        ("NET IMPORTS", net_l, net_l - net_p, "kbd", 1, BLUE),
        ("REFINERY UTIL.", util_l, util_l - util_p, "%", 1, PURPLE),
        ("CRUDE STOCKS", stk_l, stk_l - stk_p, "mb", 1000, ORANGE),
        ("STOCK CHANGE", stk_chg, stk_chg - stk_chg_prior if pd.notna(stk_chg_prior) else np.nan, "mb", 1000, RED),
        ("PRODUCTS SUPPLIED", ps_l, ps_l - ps_p, "kbd", 1, GRAY_800),
    ]

    cols = []
    for title, val, chg, unit, div, color in cards_data:
        cols.append(dbc.Col(
            _metric_card(title, _fmt(val, unit, div), _fmt_change(chg, unit, div), chg >= 0 if pd.notna(chg) else True, color),
            lg=2, md=4, sm=6,
        ))
    return dbc.Row(cols, className="mb-4")


# ---------------------------------------------------------------------------
# AG Grid column definitions
# ---------------------------------------------------------------------------

NUMBER_FMT = {"function": "params.value == null ? '' : params.data.uom === 'pct' ? params.value.toFixed(1) + '%' : params.data.uom === 'mb' ? params.value.toLocaleString('en-US', {minimumFractionDigits: 1, maximumFractionDigits: 1}) : params.value.toLocaleString('en-US', {maximumFractionDigits: 0})"}

CHANGE_FMT = {"function": "params.value == null ? '' : (params.value >= 0 ? '+' : '') + (params.data.uom === 'pct' ? params.value.toFixed(1) + '%' : params.data.uom === 'mb' ? params.value.toLocaleString('en-US', {minimumFractionDigits: 1, maximumFractionDigits: 1}) : params.value.toLocaleString('en-US', {maximumFractionDigits: 0}))"}

CHANGE_STYLE = {"styleConditions": [
    {"condition": "params.value > 0", "style": {"color": POSITIVE, "fontWeight": "600"}},
    {"condition": "params.value < 0", "style": {"color": NEGATIVE, "fontWeight": "600"}},
]}

HEADER_ROW_STYLE = {"styleConditions": [
    {
        "condition": "params.data.is_header",
        "style": {"backgroundColor": GRAY_200, "fontWeight": "700", "fontSize": "0.85rem"},
    },
]}


ITEM_STYLE = {"styleConditions": [
    {"condition": "params.data.is_header", "style": {"fontWeight": "700", "fontSize": "0.85rem"}},
    {"condition": "params.data.indent === 1", "style": {"paddingLeft": "24px", "fontWeight": "600"}},
    {"condition": "params.data.indent === 2", "style": {"paddingLeft": "48px", "color": GRAY_500, "fontSize": "0.8rem"}},
]}


def _build_grid_col_defs(latest_date, prior_date, yago_date):
    return [
        {"headerName": "Item", "field": "item", "minWidth": 250, "flex": 1, "pinned": "left", "cellStyle": ITEM_STYLE},
        {"headerName": f"Latest ({latest_date})", "field": "latest", "minWidth": 90, "maxWidth": 130, "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": f"Prior ({prior_date})", "field": "prior", "minWidth": 90, "maxWidth": 130, "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": "W/W Chg", "field": "wow", "minWidth": 80, "maxWidth": 110, "type": "numericColumn", "valueFormatter": CHANGE_FMT, "cellStyle": CHANGE_STYLE},
        {"headerName": f"Year Ago ({yago_date})", "field": "year_ago", "minWidth": 90, "maxWidth": 140, "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": "Y/Y Chg", "field": "yoy", "minWidth": 80, "maxWidth": 110, "type": "numericColumn", "valueFormatter": CHANGE_FMT, "cellStyle": CHANGE_STYLE},
        {"headerName": "5-Yr Avg", "field": "five_yr", "minWidth": 80, "maxWidth": 120, "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": "vs 5-Yr", "field": "vs_5yr", "minWidth": 80, "maxWidth": 110, "type": "numericColumn", "valueFormatter": CHANGE_FMT, "cellStyle": CHANGE_STYLE},
    ]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

# Pre-build data for initial render
_initial = build_balance_data()

layout = html.Div([
    # Title
    html.Div([
        html.Div("US PETROLEUM BALANCE", style={
            "fontSize": "0.75rem", "fontWeight": "700",
            "letterSpacing": "0.08em", "color": GRAY_500,
            "marginBottom": "0.25rem",
        }),
        html.H2("Supply / Demand Balance", style={
            "fontSize": "1.75rem", "fontWeight": "700",
            "color": GRAY_800, "margin": "0",
        }),
    ], style={"marginBottom": "1.5rem"}),

    # KPI Strip
    _build_kpi_strip(),

    # Balance Table
    dbc.Card([
        dbc.CardBody([
            dag.AgGrid(
                id="balance-grid-p14",
                rowData=_initial["rows"] if _initial else [],
                columnDefs=_build_grid_col_defs(
                    _initial["latest_date"] if _initial else "",
                    _initial["prior_date"] if _initial else "",
                    _initial["yago_date"] if _initial else "",
                ),
                defaultColDef={"resizable": True, "sortable": False, "filter": False},
                dashGridOptions={
                    "domLayout": "autoHeight",
                    "suppressRowHoverHighlight": False,
                    "getRowStyle": {"styleConditions": [
                        {
                            "condition": "params.data.is_header",
                            "style": {"backgroundColor": GRAY_200, "fontWeight": "700"},
                        },
                        {
                            "condition": "params.data.indent === 1",
                            "style": {"fontWeight": "600"},
                        },
                        {
                            "condition": "params.data.indent === 2",
                            "style": {"color": GRAY_500, "fontSize": "0.8rem"},
                        },
                    ]},
                },
                className="ag-theme-alpine",
                style={"width": "100%"},
            ),
        ], style={"padding": "0.75rem"}),
    ], style={
        "backgroundColor": "white",
        "borderRadius": "4px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
        "border": f"1px solid {GRAY_200}",
        "marginBottom": "1.5rem",
    }),

    # Product selector
    html.Div([
        html.Div("PRODUCT VIEW", style={
            "fontSize": "0.75rem", "fontWeight": "700",
            "letterSpacing": "0.08em", "color": GRAY_500,
            "marginBottom": "0.5rem",
        }),
        dbc.RadioItems(
            id="product-selector-p14",
            options=[
                {"label": "Crude Oil", "value": "crude"},
                {"label": "Gasoline", "value": "gasoline"},
                {"label": "Distillate", "value": "distillate"},
                {"label": "Jet Fuel", "value": "jet"},
            ],
            value="crude",
            inline=True,
            className="mb-3",
            inputStyle={"marginRight": "5px"},
            labelStyle={"marginRight": "1.5rem", "fontWeight": "500"},
        ),
    ], style={"marginBottom": "0.5rem"}),

    # Charts Row 1: Balance over time + Demand seasonality
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="balance-timeseries-p14", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="demand-seasonal-p14", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
    ], className="mb-4"),

    # Charts Row 2: Stock change vs seasonal + Days of supply
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="stock-surprise-p14", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="days-of-supply-p14", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
    ], className="mb-4"),

    # Hidden store for pivot data
    dcc.Store(id="pivot-store-p14", data=_initial["pivot_json"] if _initial else None),

], style=PAGE_STYLE)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def _rebuild_df(pivot_json):
    """Reconstruct DataFrame from stored JSON."""
    if not pivot_json:
        return pd.DataFrame()
    df = pd.read_json(pivot_json, orient="split")
    df["period"] = pd.to_datetime(df["period"])
    return df.sort_values("period").reset_index(drop=True)


@callback(
    Output("balance-timeseries-p14", "figure"),
    Input("product-selector-p14", "value"),
    Input("pivot-store-p14", "data"),
)
def update_balance_timeseries(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    # Last 2 years of data
    cutoff = df["period"].max() - pd.Timedelta(days=730)
    df = df[df["period"] >= cutoff].copy()

    fig = go.Figure()

    prod_sid = SERIES[cfg["prod"]]
    imp_sid = SERIES[cfg["imp"]]
    exp_sid = SERIES[cfg["exp"]]
    demand_sid = SERIES[cfg["demand"]]
    stock_sid = SERIES[cfg["stock"]]

    # Production - filled area
    if prod_sid in df.columns:
        fig.add_trace(go.Scatter(
            x=df["period"], y=df[prod_sid],
            name="Production", mode="lines",
            line=dict(color=GREEN, width=0),
            fill="tozeroy", fillcolor="rgba(74, 176, 77, 0.3)",
        ))

    # Imports - line
    if imp_sid in df.columns:
        fig.add_trace(go.Scatter(
            x=df["period"], y=df[imp_sid],
            name="Imports", mode="lines",
            line=dict(color=BLUE, width=2),
        ))

    # Exports - line (shown as positive, labeled)
    if exp_sid in df.columns:
        fig.add_trace(go.Scatter(
            x=df["period"], y=df[exp_sid],
            name="Exports", mode="lines",
            line=dict(color=ORANGE, width=2),
        ))

    # Demand / Refinery runs - line
    if demand_sid in df.columns:
        fig.add_trace(go.Scatter(
            x=df["period"], y=df[demand_sid],
            name=cfg["demand_label"], mode="lines",
            line=dict(color=RED, width=2.5),
        ))

    # Stock change as bars
    if stock_sid in df.columns:
        stk = df[stock_sid].diff() / 7  # convert kb delta to kbd
        fig.add_trace(go.Bar(
            x=df["period"], y=stk,
            name="Stock Change (kbd)",
            marker_color=[POSITIVE if v >= 0 else NEGATIVE for v in stk.fillna(0)],
            opacity=0.4,
        ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — Balance Over Time (kbd)", font=dict(size=14))
    layout["yaxis"]["title"] = "kbd"
    layout["barmode"] = "relative"
    fig.update_layout(**layout)
    return fig


@callback(
    Output("demand-seasonal-p14", "figure"),
    Input("product-selector-p14", "value"),
    Input("pivot-store-p14", "data"),
)
def update_demand_seasonal(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    demand_sid = SERIES[cfg["demand"]]
    if demand_sid not in df.columns:
        return go.Figure().update_layout(title="Data not available")

    fig = go.Figure()

    # 5-year range band
    stats = _five_year_stats(df, demand_sid)
    if not stats.empty:
        fig.add_trace(go.Scatter(
            x=stats["week"], y=stats["max"],
            mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=stats["week"], y=stats["min"],
            mode="lines", line=dict(width=0), fill="tonexty",
            fillcolor="rgba(0,0,0,0.06)", name="5-Yr Range", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=stats["week"], y=stats["mean"],
            mode="lines", line=dict(color=GRAY_300, width=1.5, dash="dash"),
            name="5-Yr Avg",
        ))

    # Year-ago
    current_year = df["period"].dt.year.max()
    ya_mask = df["period"].dt.year == (current_year - 1)
    ya = df.loc[ya_mask].copy()
    if not ya.empty:
        ya["week"] = ya["period"].dt.isocalendar().week.astype(int)
        fig.add_trace(go.Scatter(
            x=ya["week"], y=ya[demand_sid],
            mode="lines", line=dict(color=BLUE, width=1.5),
            name=str(current_year - 1),
        ))

    # Current year
    cur_mask = df["period"].dt.year == current_year
    cur = df.loc[cur_mask].copy()
    if not cur.empty:
        cur["week"] = cur["period"].dt.isocalendar().week.astype(int)
        fig.add_trace(go.Scatter(
            x=cur["week"], y=cur[demand_sid],
            mode="lines", line=dict(color=BLACK, width=2.5),
            name=str(current_year),
        ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — {cfg['demand_label']} Seasonality (kbd)", font=dict(size=14))
    layout["xaxis"]["title"] = "Week of Year"
    layout["yaxis"]["title"] = "kbd"
    fig.update_layout(**layout)
    return fig


@callback(
    Output("stock-surprise-p14", "figure"),
    Input("product-selector-p14", "value"),
    Input("pivot-store-p14", "data"),
)
def update_stock_surprise(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    stock_sid = SERIES[cfg["stock"]]
    if stock_sid not in df.columns:
        return go.Figure().update_layout(title="Data not available")

    # Compute weekly stock changes
    df["stk_chg"] = df[stock_sid].diff()
    df["week"] = df["period"].dt.isocalendar().week.astype(int)

    # 5-year seasonal average stock change
    mask_5yr = df["period"].dt.year.isin(years_last_five_years_range)
    seasonal_avg = df.loc[mask_5yr].groupby("week")["stk_chg"].mean()

    # Last 12 weeks
    recent = df.tail(12).copy()
    if recent.empty:
        return go.Figure().update_layout(title="No data available")

    recent["seasonal_avg"] = recent["week"].map(seasonal_avg)
    recent["surprise"] = recent["stk_chg"] - recent["seasonal_avg"]

    fig = go.Figure()

    # Date labels for x-axis
    x_labels = recent["period"].dt.strftime("%m/%d").tolist()

    fig.add_trace(go.Bar(
        x=x_labels, y=recent["stk_chg"].values,
        name="Actual Change (kb)", marker_color=BLUE, opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        x=x_labels, y=recent["seasonal_avg"].values,
        name="5-Yr Seasonal Avg", marker_color=GRAY_300, opacity=0.8,
    ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — Stock Change vs Seasonal (kb)", font=dict(size=14))
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "kb"
    layout["xaxis"]["title"] = "Week Ending"
    fig.update_layout(**layout)
    return fig


@callback(
    Output("days-of-supply-p14", "figure"),
    Input("product-selector-p14", "value"),
    Input("pivot-store-p14", "data"),
)
def update_days_of_supply(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    stock_sid = SERIES[cfg["stock"]]
    demand_sid = SERIES[cfg["demand"]]
    if stock_sid not in df.columns or demand_sid not in df.columns:
        return go.Figure().update_layout(title="Data not available")

    # Days of supply = stocks (kb) / (demand kbd * 7)
    df["dos"] = df[stock_sid] / (df[demand_sid] * 7)
    df["week"] = df["period"].dt.isocalendar().week.astype(int)

    fig = go.Figure()

    # 5-year range band
    stats = _five_year_stats(df.assign(**{"dos_col": df["dos"]}), "dos_col")
    # Recompute properly
    mask_5yr = df["period"].dt.year.isin(years_last_five_years_range)
    sub_5yr = df.loc[mask_5yr].copy()
    if not sub_5yr.empty:
        grouped = sub_5yr.groupby("week")["dos"].agg(["mean", "min", "max"]).reset_index()
        fig.add_trace(go.Scatter(
            x=grouped["week"], y=grouped["max"],
            mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=grouped["week"], y=grouped["min"],
            mode="lines", line=dict(width=0), fill="tonexty",
            fillcolor="rgba(0,0,0,0.06)", name="5-Yr Range", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=grouped["week"], y=grouped["mean"],
            mode="lines", line=dict(color=GRAY_300, width=1.5, dash="dash"),
            name="5-Yr Avg",
        ))

    # Year-ago
    current_year = df["period"].dt.year.max()
    ya = df[df["period"].dt.year == (current_year - 1)].copy()
    if not ya.empty:
        fig.add_trace(go.Scatter(
            x=ya["week"], y=ya["dos"],
            mode="lines", line=dict(color=BLUE, width=1.5),
            name=str(current_year - 1),
        ))

    # Current year
    cur = df[df["period"].dt.year == current_year].copy()
    if not cur.empty:
        fig.add_trace(go.Scatter(
            x=cur["week"], y=cur["dos"],
            mode="lines", line=dict(color=BLACK, width=2.5),
            name=str(current_year),
        ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — Days of Supply", font=dict(size=14))
    layout["xaxis"]["title"] = "Week of Year"
    layout["yaxis"]["title"] = "Days"
    fig.update_layout(**layout)
    return fig
