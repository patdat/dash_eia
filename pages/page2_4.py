import pandas as pd
import numpy as np
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go
from src.utils.data_loader import loader
from src.utils.colors import (
    RED, BLUE, GREEN, ORANGE, PURPLE, BLACK,
    POSITIVE, NEGATIVE, COLORSCALE_HEATMAP,
    CHART_SEQUENCE, GRAY_50, GRAY_200, GRAY_300, GRAY_500, GRAY_800,
)
from src.utils.variables import years_last_five_years_range

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_STYLE = {"padding": "2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"}
CHART_HEIGHT = 440
PADD_REGIONS = ['P1', 'P2', 'P3', 'P4', 'P5']
PADD_COLORS = {
    'P1': RED, 'P2': BLUE, 'P3': ORANGE, 'P4': GREEN, 'P5': PURPLE,
}

CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
    height=CHART_HEIGHT,
    margin=dict(l=60, r=20, t=70, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                font=dict(size=11)),
    font=dict(family="Montserrat"),
    xaxis=dict(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300),
    yaxis=dict(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300),
)

PADD_LABELS = {
    'US': 'United States',
    'P1': 'PADD 1 — East Coast',
    'P2': 'PADD 2 — Midwest',
    'P3': 'PADD 3 — Gulf Coast',
    'P4': 'PADD 4 — Rocky Mountain',
    'P5': 'PADD 5 — West Coast',
}

PADD_LABELS_SHORT = {
    'US': 'US Total', 'P1': 'East Coast', 'P2': 'Midwest',
    'P3': 'Gulf Coast', 'P4': 'Rocky Mtn', 'P5': 'West Coast',
}

# ---------------------------------------------------------------------------
# Series ID Mapping
# ---------------------------------------------------------------------------
PADD_SERIES = {
    'US': {
        'crude_stocks': 'WCESTUS1', 'gas_stocks': 'WGTSTUS1',
        'dist_stocks': 'WDISTUS1', 'jet_stocks': 'WKJSTUS1',
        'crude_imports': 'WCEIMUS2', 'gas_imports': 'WGTIMUS2',
        'dist_imports': 'WDIIMUS2', 'jet_imports': 'WKJIMUS2',
        'crude_runs': 'WCRRIUS2', 'gas_prod': 'WGFRPUS2',
        'dist_prod': 'WDIRPUS2', 'jet_prod': 'WKJRPUS2',
    },
    'P1': {
        'crude_stocks': 'WCESTP11', 'gas_stocks': 'WGTSTP11',
        'dist_stocks': 'WDISTP11', 'jet_stocks': 'WKJSTP11',
        'crude_imports': 'WCEIMP12', 'gas_imports': 'WGTIM_R10-Z00_2',
        'dist_imports': 'WDIIM_R10-Z00_2', 'jet_imports': 'WKJIM_R10-Z00_2',
        'crude_runs': 'WCRRIP12', 'gas_prod': 'WGFRPP12',
        'dist_prod': 'WDIRPP12', 'jet_prod': 'WKJRPP12',
    },
    'P2': {
        'crude_stocks': 'WCESTP21', 'gas_stocks': 'WGTSTP21',
        'dist_stocks': 'WDISTP21', 'jet_stocks': 'WKJSTP21',
        'crude_imports': 'WCEIMP22', 'gas_imports': 'WGTIM_R20-Z00_2',
        'dist_imports': 'WDIIM_R20-Z00_2', 'jet_imports': 'WKJIM_R20-Z00_2',
        'crude_runs': 'WCRRIP22', 'gas_prod': 'WGFRPP22',
        'dist_prod': 'WDIRPP22', 'jet_prod': 'WKJRPP22',
    },
    'P3': {
        'crude_stocks': 'WCESTP31', 'gas_stocks': 'WGTSTP31',
        'dist_stocks': 'WDISTP31', 'jet_stocks': 'WKJSTP31',
        'crude_imports': 'WCEIMP32', 'gas_imports': 'WGTIM_R30-Z00_2',
        'dist_imports': 'WDIIM_R30-Z00_2', 'jet_imports': 'WKJIM_R30-Z00_2',
        'crude_runs': 'WCRRIP32', 'gas_prod': 'WGFRPP32',
        'dist_prod': 'WDIRPP32', 'jet_prod': 'WKJRPP32',
    },
    'P4': {
        'crude_stocks': 'WCESTP41', 'gas_stocks': 'WGTSTP41',
        'dist_stocks': 'WDISTP41', 'jet_stocks': 'WKJSTP41',
        'crude_imports': 'WCEIMP42', 'gas_imports': 'WGTIM_R40-Z00_2',
        'dist_imports': 'WDIIM_R40-Z00_2', 'jet_imports': 'WKJIM_R40-Z00_2',
        'crude_runs': 'WCRRIP42', 'gas_prod': 'WGFRPP42',
        'dist_prod': 'WDIRPP42', 'jet_prod': 'WKJRPP42',
    },
    'P5': {
        'crude_stocks': 'WCESTP51', 'gas_stocks': 'WGTSTP51',
        'dist_stocks': 'WDISTP51', 'jet_stocks': 'WKJSTP51',
        'crude_imports': 'WCEIMP52', 'gas_imports': 'WGTIM_R50-Z00_2',
        'dist_imports': 'WDIIM_R50-Z00_2', 'jet_imports': 'WKJIM_R50-Z00_2',
        'crude_runs': 'WCRRIP52', 'gas_prod': 'WGFRPP52',
        'dist_prod': 'WDIRPP52', 'jet_prod': 'WKJRPP52',
    },
}

PRODUCT_CONFIG = {
    'crude': {
        'stock': 'crude_stocks', 'import': 'crude_imports',
        'demand': 'crude_runs', 'label': 'Crude Oil',
        'demand_label': 'Refinery Runs',
    },
    'gasoline': {
        'stock': 'gas_stocks', 'import': 'gas_imports',
        'demand': 'gas_prod', 'label': 'Gasoline',
        'demand_label': 'Production',
    },
    'distillate': {
        'stock': 'dist_stocks', 'import': 'dist_imports',
        'demand': 'dist_prod', 'label': 'Distillate',
        'demand_label': 'Production',
    },
    'jet': {
        'stock': 'jet_stocks', 'import': 'jet_imports',
        'demand': 'jet_prod', 'label': 'Jet Fuel',
        'demand_label': 'Production',
    },
}


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_pivot():
    df = loader.load_wps_pivot_data()
    df = df.sort_values("period").reset_index(drop=True)
    return df


def _find_year_ago(df, target_period):
    target = target_period - pd.Timedelta(days=364)
    idx = (df["period"] - target).abs().idxmin()
    return df.loc[idx]


def _five_year_avg(df, target_week, col):
    mask = (df["period"].dt.isocalendar().week.astype(int) == target_week) & (
        df["period"].dt.year.isin(years_last_five_years_range)
    )
    subset = df.loc[mask, col]
    return subset.mean() if len(subset) > 0 else np.nan


def _five_year_stats(df, col):
    mask = df["period"].dt.year.isin(years_last_five_years_range)
    sub = df.loc[mask].copy()
    sub["week"] = sub["period"].dt.isocalendar().week.astype(int)
    if col not in sub.columns:
        return pd.DataFrame(columns=["week", "mean", "min", "max"])
    return sub.groupby("week")[col].agg(["mean", "min", "max"]).reset_index()


def _hex_to_rgba(hex_color, alpha=0.4):
    """Convert hex color to rgba string with given alpha."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _safe_val(df_row, sid):
    try:
        v = df_row[sid]
        return float(v) if pd.notna(v) else np.nan
    except (KeyError, TypeError):
        return np.nan


def _get_sid(product, padd, key_type):
    """Get series ID for a product/padd/key_type combo."""
    cfg = PRODUCT_CONFIG[product]
    key = cfg[key_type]
    return PADD_SERIES[padd].get(key)


# ---------------------------------------------------------------------------
# KPI card builder (same pattern as page2_7)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# AG Grid formatters (same pattern as page2_7)
# ---------------------------------------------------------------------------

NUMBER_FMT = {"function": """
    if (params.value == null) return '';
    return params.value.toLocaleString('en-US', {maximumFractionDigits: 0});
"""}

CHANGE_FMT = {"function": """
    if (params.value == null) return '';
    var sign = params.value >= 0 ? '+' : '';
    return sign + params.value.toLocaleString('en-US', {maximumFractionDigits: 0});
"""}

CHANGE_STYLE = {"styleConditions": [
    {"condition": "params.value > 0", "style": {"color": POSITIVE, "fontWeight": "600"}},
    {"condition": "params.value < 0", "style": {"color": NEGATIVE, "fontWeight": "600"}},
]}

DAYS_FMT = {"function": """
    if (params.value == null) return '';
    return params.value.toFixed(1);
"""}


# ---------------------------------------------------------------------------
# Pre-load data
# ---------------------------------------------------------------------------

try:
    _initial_df = _load_pivot()
    _initial_json = _initial_df.to_json(date_format="iso", orient="split")
except Exception as e:
    print(f"Error loading initial data for page2_4: {e}")
    _initial_df = pd.DataFrame()
    _initial_json = None


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    # Title + Product selector
    html.Div([
        html.Div([
            html.Div("REGIONAL PETROLEUM OVERVIEW", style={
                "fontSize": "0.75rem", "fontWeight": "700",
                "letterSpacing": "0.08em", "color": GRAY_500,
                "marginBottom": "0.25rem",
            }),
            html.H2("PADD Analysis", style={
                "fontSize": "1.75rem", "fontWeight": "700",
                "color": GRAY_800, "margin": "0",
            }),
        ]),
        html.Div([
            html.Div("PRODUCT", style={
                "fontSize": "0.7rem", "fontWeight": "700",
                "letterSpacing": "0.08em", "color": GRAY_500,
                "marginBottom": "0.25rem",
            }),
            dbc.RadioItems(
                id="product-selector-p11",
                options=[
                    {"label": "Crude Oil", "value": "crude"},
                    {"label": "Gasoline", "value": "gasoline"},
                    {"label": "Distillate", "value": "distillate"},
                    {"label": "Jet Fuel", "value": "jet"},
                ],
                value="crude",
                inline=True,
                inputStyle={"marginRight": "5px"},
                labelStyle={"marginRight": "1.5rem", "fontWeight": "500"},
            ),
        ]),
    ], style={"display": "flex", "justifyContent": "space-between",
              "alignItems": "flex-end", "marginBottom": "1.5rem"}),

    # KPI Strip
    html.Div(id="kpi-strip-p11", style={"marginBottom": "1.5rem"}),

    # AG Grid: PADD Comparison Table
    dbc.Card([
        dbc.CardBody([
            dag.AgGrid(
                id="padd-grid-p11",
                rowData=[],
                columnDefs=[],
                defaultColDef={"resizable": True, "sortable": True, "filter": False},
                dashGridOptions={
                    "domLayout": "autoHeight",
                    "suppressRowHoverHighlight": False,
                },
                className="ag-theme-alpine",
                style={"width": "100%"},
            ),
        ], style={"padding": "0.75rem"}),
    ], style={
        "backgroundColor": "white", "borderRadius": "4px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
        "border": f"1px solid {GRAY_200}", "marginBottom": "1.5rem",
    }),

    # Row 1: Stacked Area + Stock Concentration
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="stocks-stacked-p11", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="stock-share-p11", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
    ], className="mb-4"),

    # Row 2: Weekly Changes + Days of Supply Heatmap
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="weekly-changes-p11", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="dos-heatmap-p11", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
    ], className="mb-4"),

    # Row 3: Seasonality + Import Dependency
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Div("PADD:", style={"fontSize": "0.75rem", "fontWeight": "600",
                                             "color": GRAY_500, "marginRight": "8px",
                                             "alignSelf": "center"}),
                    dcc.Dropdown(
                        id="padd-selector-p11",
                        options=[{"label": v, "value": k} for k, v in PADD_LABELS.items()],
                        value="US",
                        clearable=False,
                        style={"width": "220px"},
                    ),
                ], style={"display": "flex", "marginBottom": "8px"}),
                dcc.Graph(id="seasonality-p11", config={"displayModeBar": False}),
            ])
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
        dbc.Col(dbc.Card([
            dbc.CardBody(dcc.Graph(id="import-dependency-p11", config={"displayModeBar": False}))
        ], style={"backgroundColor": "white", "borderRadius": "4px",
                  "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {GRAY_200}"}),
            lg=6),
    ], className="mb-4"),

    # Hidden store
    dcc.Store(id="pivot-store-p11", data=_initial_json),

], style=PAGE_STYLE)


# ---------------------------------------------------------------------------
# Helper: reconstruct DataFrame from store
# ---------------------------------------------------------------------------

def _rebuild_df(pivot_json):
    if not pivot_json:
        return pd.DataFrame()
    df = pd.read_json(pivot_json, orient="split")
    df["period"] = pd.to_datetime(df["period"])
    return df.sort_values("period").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Callback 1: KPI Strip
# ---------------------------------------------------------------------------

@callback(
    Output("kpi-strip-p11", "children"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_kpi_strip(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return dbc.Row(html.Div("No data available.", style={"color": GRAY_500}))

    latest = df.iloc[-1]
    prior = df.iloc[-2] if len(df) >= 2 else latest

    cols = []
    regions = PADD_REGIONS + ['US']
    colors = [PADD_COLORS[p] for p in PADD_REGIONS] + [GRAY_800]

    for padd, color in zip(regions, colors):
        sid = _get_sid(product, padd, 'stock')
        if sid is None:
            continue
        lv = _safe_val(latest, sid)
        pv = _safe_val(prior, sid)
        chg = lv - pv if pd.notna(lv) and pd.notna(pv) else np.nan

        if pd.notna(lv):
            val_str = f"{lv / 1000:,.1f} mb"
        else:
            val_str = "—"

        if pd.notna(chg):
            sign = "+" if chg >= 0 else ""
            chg_str = f"{sign}{chg / 1000:,.1f} mb"
        else:
            chg_str = "—"

        label = PADD_LABELS_SHORT.get(padd, padd)
        cols.append(dbc.Col(
            _metric_card(label, val_str, chg_str,
                         chg >= 0 if pd.notna(chg) else True, color),
            lg=2, md=4, sm=6,
        ))

    return dbc.Row(cols)


# ---------------------------------------------------------------------------
# Callback 2: AG Grid — PADD Comparison Table
# ---------------------------------------------------------------------------

@callback(
    Output("padd-grid-p11", "rowData"),
    Output("padd-grid-p11", "columnDefs"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_padd_grid(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return [], []

    latest = df.iloc[-1]
    prior = df.iloc[-2] if len(df) >= 2 else latest
    yago = _find_year_ago(df, latest["period"])
    latest_week = int(latest["period"].isocalendar().week)
    cfg = PRODUCT_CONFIG[product]

    rows = []
    for padd in PADD_REGIONS + ['US']:
        stock_sid = _get_sid(product, padd, 'stock')
        imp_sid = _get_sid(product, padd, 'import')
        demand_sid = _get_sid(product, padd, 'demand')

        stk_l = _safe_val(latest, stock_sid) if stock_sid else np.nan
        stk_p = _safe_val(prior, stock_sid) if stock_sid else np.nan
        stk_y = _safe_val(yago, stock_sid) if stock_sid else np.nan
        stk_5yr = _five_year_avg(df, latest_week, stock_sid) if stock_sid else np.nan

        imp_l = _safe_val(latest, imp_sid) if imp_sid else np.nan
        dem_l = _safe_val(latest, demand_sid) if demand_sid else np.nan

        wow = stk_l - stk_p if pd.notna(stk_l) and pd.notna(stk_p) else None
        yoy = stk_l - stk_y if pd.notna(stk_l) and pd.notna(stk_y) else None
        vs5 = stk_l - stk_5yr if pd.notna(stk_l) and pd.notna(stk_5yr) else None

        dos = stk_l / (dem_l * 7) if pd.notna(stk_l) and pd.notna(dem_l) and dem_l > 0 else None

        rows.append({
            "region": PADD_LABELS_SHORT.get(padd, padd),
            "stocks": round(stk_l) if pd.notna(stk_l) else None,
            "wow": round(wow) if wow is not None else None,
            "yoy": round(yoy) if yoy is not None else None,
            "vs_5yr": round(vs5) if vs5 is not None else None,
            "imports": round(imp_l) if pd.notna(imp_l) else None,
            "demand": round(dem_l) if pd.notna(dem_l) else None,
            "dos": round(dos, 1) if dos is not None else None,
            "is_total": padd == 'US',
        })

    latest_str = latest["period"].strftime("%m/%d")
    col_defs = [
        {"headerName": "Region", "field": "region", "width": 140, "pinned": "left",
         "cellStyle": {"styleConditions": [
             {"condition": "params.data.is_total", "style": {"fontWeight": "700", "backgroundColor": GRAY_50}},
         ]}},
        {"headerName": f"Stocks ({latest_str})", "field": "stocks", "width": 140,
         "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": "W/W Chg", "field": "wow", "width": 110,
         "type": "numericColumn", "valueFormatter": CHANGE_FMT, "cellStyle": CHANGE_STYLE},
        {"headerName": "Y/Y Chg", "field": "yoy", "width": 110,
         "type": "numericColumn", "valueFormatter": CHANGE_FMT, "cellStyle": CHANGE_STYLE},
        {"headerName": "vs 5-Yr", "field": "vs_5yr", "width": 110,
         "type": "numericColumn", "valueFormatter": CHANGE_FMT, "cellStyle": CHANGE_STYLE},
        {"headerName": "Imports (kbd)", "field": "imports", "width": 130,
         "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": cfg['demand_label'] + " (kbd)", "field": "demand", "width": 150,
         "type": "numericColumn", "valueFormatter": NUMBER_FMT},
        {"headerName": "Days of Supply", "field": "dos", "width": 130,
         "type": "numericColumn", "valueFormatter": DAYS_FMT},
    ]

    return rows, col_defs


# ---------------------------------------------------------------------------
# Callback 3: Stacked Area — Regional Stocks
# ---------------------------------------------------------------------------

@callback(
    Output("stocks-stacked-p11", "figure"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_stocks_stacked(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    cutoff = df["period"].max() - pd.Timedelta(days=730)
    df = df[df["period"] >= cutoff].copy()

    fig = go.Figure()

    # Sort PADDs by latest value (largest first) so biggest region is at bottom of stack
    padd_vals = []
    for padd in PADD_REGIONS:
        sid = _get_sid(product, padd, 'stock')
        if sid and sid in df.columns:
            last_val = df[sid].iloc[-1] if pd.notna(df[sid].iloc[-1]) else 0
            padd_vals.append((padd, sid, last_val))
    padd_vals.sort(key=lambda x: x[2], reverse=True)

    # Stacked areas — largest region at bottom for better visual
    dates = df["period"].tolist()
    for padd, sid, _ in padd_vals:
        fig.add_trace(go.Scatter(
            x=dates, y=df[sid].tolist(),
            name=PADD_LABELS_SHORT[padd], mode="lines",
            line=dict(width=0.5, color=PADD_COLORS[padd]),
            stackgroup="one",
            fillcolor=_hex_to_rgba(PADD_COLORS[padd], 0.6),
        ))

    # US total as dashed overlay
    us_sid = _get_sid(product, 'US', 'stock')
    if us_sid and us_sid in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df[us_sid].tolist(),
            name="US Total", mode="lines",
            line=dict(color=BLACK, width=2.5, dash="dash"),
        ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — Regional Stock Levels (kb)", font=dict(size=14))
    layout["yaxis"]["title"] = "kb"
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Callback 4: Stock Concentration — 100% Stacked Area
# ---------------------------------------------------------------------------

@callback(
    Output("stock-share-p11", "figure"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_stock_share(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    cutoff = df["period"].max() - pd.Timedelta(days=730)
    df = df[df["period"] >= cutoff].copy()

    # Compute US total for denominator
    us_sid = _get_sid(product, 'US', 'stock')
    if not us_sid or us_sid not in df.columns:
        return go.Figure().update_layout(title="US total not available")

    fig = go.Figure()

    dates = df["period"].tolist()
    for padd in PADD_REGIONS:
        sid = _get_sid(product, padd, 'stock')
        if sid and sid in df.columns:
            fig.add_trace(go.Scatter(
                x=dates, y=df[sid].tolist(),
                name=PADD_LABELS_SHORT[padd], mode="lines",
                line=dict(width=0.5, color=PADD_COLORS[padd]),
                stackgroup="one",
                groupnorm="percent",
                fillcolor=_hex_to_rgba(PADD_COLORS[padd], 0.55),
            ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — Stock Concentration by PADD (%)", font=dict(size=14))
    layout["yaxis"]["title"] = "% of US Total"
    layout["yaxis"]["range"] = [0, 100]
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Callback 5: Weekly Stock Changes — Grouped Bar
# ---------------------------------------------------------------------------

@callback(
    Output("weekly-changes-p11", "figure"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_weekly_changes(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    recent = df.tail(9).copy()  # 9 rows to get 8 diffs
    if len(recent) < 2:
        return go.Figure().update_layout(title="Insufficient data")

    fig = go.Figure()
    plot_df = recent.iloc[1:].copy()
    x_labels = plot_df["period"].dt.strftime("%m/%d").tolist()

    for padd in PADD_REGIONS:
        sid = _get_sid(product, padd, 'stock')
        if sid and sid in recent.columns:
            changes = recent[sid].diff().iloc[1:].tolist()
            fig.add_trace(go.Bar(
                x=x_labels, y=changes,
                name=PADD_LABELS_SHORT[padd],
                marker_color=PADD_COLORS[padd],
            ))

    # Add a net total line
    total_changes = []
    for i in range(len(plot_df)):
        net = 0
        for padd in PADD_REGIONS:
            sid = _get_sid(product, padd, 'stock')
            if sid and sid in recent.columns:
                chg = recent[sid].diff().iloc[i + 1]
                if pd.notna(chg):
                    net += chg
        total_changes.append(net)

    fig.add_trace(go.Scatter(
        x=x_labels, y=total_changes,
        name="Net Total", mode="lines+markers",
        line=dict(color=BLACK, width=2.5),
        marker=dict(size=6),
    ))

    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=f"{cfg['label']} — Weekly Stock Changes by PADD (kb)", font=dict(size=14))
    layout["barmode"] = "relative"
    layout["yaxis"]["title"] = "kb"
    layout["xaxis"]["title"] = "Week Ending"
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Callback 6: Days of Supply Heatmap (REAL DATA)
# ---------------------------------------------------------------------------

@callback(
    Output("dos-heatmap-p11", "figure"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_dos_heatmap(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    latest = df.iloc[-1]
    products = ['crude', 'gasoline', 'distillate', 'jet']
    product_labels = ['Crude', 'Gasoline', 'Distillate', 'Jet']

    z_data = []
    for prod in products:
        row_vals = []
        for padd in PADD_REGIONS:
            stock_sid = _get_sid(prod, padd, 'stock')
            demand_sid = _get_sid(prod, padd, 'demand')
            stk = _safe_val(latest, stock_sid) if stock_sid else np.nan
            dem = _safe_val(latest, demand_sid) if demand_sid else np.nan
            if pd.notna(stk) and pd.notna(dem) and dem > 0:
                dos = stk / (dem * 7)
                row_vals.append(round(dos, 1))
            else:
                row_vals.append(None)
        z_data.append(row_vals)

    # Create text annotations
    text_data = []
    for row in z_data:
        text_row = []
        for val in row:
            text_row.append(f"{val:.1f}" if val is not None else "N/A")
        text_data.append(text_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[PADD_LABELS_SHORT[p] for p in PADD_REGIONS],
        y=product_labels,
        colorscale=COLORSCALE_HEATMAP,
        text=text_data,
        texttemplate="%{text} days",
        textfont={"size": 14},
        hoverongaps=False,
        colorbar=dict(title="Days"),
    ))

    fig.update_layout(
        title=dict(text="Days of Supply by Product & PADD", font=dict(size=14)),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Montserrat"),
        height=CHART_HEIGHT,
        margin=dict(l=80, r=20, t=50, b=40),
        xaxis=dict(side="bottom"),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ---------------------------------------------------------------------------
# Callback 7: Stocks Seasonality
# ---------------------------------------------------------------------------

@callback(
    Output("seasonality-p11", "figure"),
    Input("product-selector-p11", "value"),
    Input("padd-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_seasonality(product, padd, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    sid = _get_sid(product, padd, 'stock')
    if not sid or sid not in df.columns:
        return go.Figure().update_layout(title="Data not available")

    fig = go.Figure()

    # 5-year range band
    stats = _five_year_stats(df, sid)
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

    # Year-ago line
    current_year = df["period"].dt.year.max()
    df_copy = df.copy()
    df_copy["week"] = df_copy["period"].dt.isocalendar().week.astype(int)

    ya_mask = df_copy["period"].dt.year == (current_year - 1)
    ya = df_copy.loc[ya_mask]
    if not ya.empty:
        fig.add_trace(go.Scatter(
            x=ya["week"], y=ya[sid],
            mode="lines", line=dict(color=BLUE, width=1.5),
            name=str(current_year - 1),
        ))

    # Current year
    cur_mask = df_copy["period"].dt.year == current_year
    cur = df_copy.loc[cur_mask]
    if not cur.empty:
        fig.add_trace(go.Scatter(
            x=cur["week"], y=cur[sid],
            mode="lines", line=dict(color=BLACK, width=2.5),
            name=str(current_year),
        ))

    padd_label = PADD_LABELS.get(padd, padd)
    layout = {**CHART_LAYOUT}
    layout["title"] = dict(
        text=f"{cfg['label']} Stocks Seasonality — {padd_label} (kb)",
        font=dict(size=14),
    )
    layout["xaxis"]["title"] = "Week of Year"
    layout["xaxis"]["range"] = [1, 52]
    layout["yaxis"]["title"] = "kb"
    layout["yaxis"]["rangemode"] = "normal"

    # Compute a tighter y-axis range from the data
    all_y = []
    for trace in fig.data:
        if trace.y is not None:
            vals = [v for v in trace.y if v is not None and not (isinstance(v, float) and pd.isna(v))]
            all_y.extend(vals)
    if all_y:
        ymin, ymax = min(all_y), max(all_y)
        pad = (ymax - ymin) * 0.08 if ymax > ymin else ymax * 0.05
        layout["yaxis"]["range"] = [ymin - pad, ymax + pad]

    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Callback 8: Import Dependency — Horizontal Bar
# ---------------------------------------------------------------------------

@callback(
    Output("import-dependency-p11", "figure"),
    Input("product-selector-p11", "value"),
    Input("pivot-store-p11", "data"),
)
def update_import_dependency(product, pivot_json):
    df = _rebuild_df(pivot_json)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    cfg = PRODUCT_CONFIG[product]
    latest = df.iloc[-1]

    padds = []
    ratios = []
    colors = []

    for padd in PADD_REGIONS:
        imp_sid = _get_sid(product, padd, 'import')
        dem_sid = _get_sid(product, padd, 'demand')

        imp_v = _safe_val(latest, imp_sid) if imp_sid else np.nan
        dem_v = _safe_val(latest, dem_sid) if dem_sid else np.nan

        if pd.notna(imp_v) and pd.notna(dem_v) and dem_v > 0:
            ratio = imp_v / dem_v * 100
            padds.append(PADD_LABELS_SHORT[padd])
            ratios.append(round(ratio, 1))
            colors.append(PADD_COLORS[padd])

    if not padds:
        return go.Figure().update_layout(title="Import data not available")

    # Sort by ratio descending
    sorted_data = sorted(zip(padds, ratios, colors), key=lambda x: x[1])
    padds, ratios, colors = zip(*sorted_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=list(padds), x=list(ratios),
        orientation="h",
        marker_color=list(colors),
        text=[f"{r:.1f}%" for r in ratios],
        textposition="outside",
        textfont=dict(size=13, color=GRAY_800),
        width=0.6,
    ))

    max_ratio = max(ratios) if ratios else 100
    x_max = max(max_ratio * 1.15, 20)

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
        height=CHART_HEIGHT,
        margin=dict(l=120, r=60, t=50, b=40),
        showlegend=False,
        font=dict(family="Montserrat"),
        title=dict(text=f"{cfg['label']} — Import Dependency by PADD", font=dict(size=14)),
        xaxis=dict(
            title=f"Imports as % of {cfg['demand_label']}",
            range=[0, x_max],
            showgrid=True, gridcolor=GRAY_200,
            showline=True, linecolor=GRAY_300,
        ),
        yaxis=dict(
            title="",
            showgrid=False,
            showline=True, linecolor=GRAY_300,
            automargin=True,
        ),
    )
    return fig
