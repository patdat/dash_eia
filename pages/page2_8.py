"""Advanced Time Series Analytics — 5-tabbed analytics suite with dark chart theme."""

import warnings
import numpy as np
import pandas as pd
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.utils.data_loader import loader
from src.utils.colors import (
    RED, BLUE, GREEN, ORANGE, PURPLE, BLACK,
    GRAY_50, GRAY_200, GRAY_500, GRAY_800,
    COLORSCALE_SEQUENTIAL, CHART_SEQUENCE,
)

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Data — load once at module level
# ---------------------------------------------------------------------------
_pivot = loader.load_wps_pivot_data().sort_values("period").reset_index(drop=True)

# ---------------------------------------------------------------------------
# Curated series
# ---------------------------------------------------------------------------
ANALYTICS_SERIES = {
    "WCESTUS1": "Crude Oil Stocks",
    "WGTSTUS1": "Gasoline Stocks",
    "WDISTUS1": "Distillate Stocks",
    "WKJSTUS1": "Jet Fuel Stocks",
    "WCRFPUS2": "Crude Production",
    "W_EPC0_FPF_R48_MBBLD": "L48 Crude Production",
    "WCEIMUS2": "Crude Imports",
    "WCREXUS2": "Crude Exports",
    "WCRRIUS2": "Refinery Inputs",
    "WPULEUS3": "Refinery Utilization",
    "WRPUPUS2": "Total Products Supplied",
    "WGFUPUS2": "Gasoline Supplied",
    "WDIUPUS2": "Distillate Supplied",
    "WKJUPUS2": "Jet Fuel Supplied",
    "WGFRPUS2": "Gasoline Production",
    "WDIRPUS2": "Distillate Production",
}

_SERIES_OPTIONS = [{"label": v, "value": k} for k, v in ANALYTICS_SERIES.items()]
_DEFAULT_SERIES = "WCESTUS1"

# Subset for cross-product analysis
_CROSS_DEFAULTS = ["WCESTUS1", "WGTSTUS1", "WDISTUS1", "WCRFPUS2", "WCRRIUS2", "WRPUPUS2"]

# ---------------------------------------------------------------------------
# Dark theme helpers
# ---------------------------------------------------------------------------
_BG = "#1a1a2e"
_BG2 = "#16213e"
_GRID = "#2a2a4a"
_TEXT = "#e0e0e0"
_ACCENT_COLORS = ["#00d4ff", "#ff6b6b", "#ffd93d", "#6bcb77", "#c084fc", "#ff922b"]


def _apply_theme(fig, height=480):
    fig.update_layout(
        plot_bgcolor=_BG,
        paper_bgcolor=_BG2,
        font=dict(family="Montserrat", color=_TEXT),
        height=height,
        margin=dict(l=60, r=20, t=50, b=40),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(color=_TEXT, size=10),
        ),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor=_GRID, showline=True, linecolor=_GRID, color=_TEXT)
    fig.update_yaxes(showgrid=True, gridcolor=_GRID, showline=True, linecolor=_GRID, color=_TEXT)
    return fig


def _empty_fig(msg="No data available", height=480):
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=16, color=_TEXT))
    _apply_theme(fig, height)
    return fig


def _get_ts(series_id):
    """Return (dates, values) as numpy arrays, dropping NaNs."""
    if series_id not in _pivot.columns:
        return np.array([]), np.array([])
    s = _pivot[["period", series_id]].dropna(subset=[series_id])
    return s["period"].values, s[series_id].values.astype(float)


# ---------------------------------------------------------------------------
# Card / layout helpers
# ---------------------------------------------------------------------------
_CARD_STYLE = {
    "backgroundColor": _BG2, "borderRadius": "8px",
    "border": f"1px solid {_GRID}", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)",
}
_PAGE_STYLE = {"padding": "1.5rem", "backgroundColor": _BG, "minHeight": "100vh"}


def _chart_card(graph_id, **kwargs):
    return dbc.Card(
        dbc.CardBody(dcc.Graph(id=graph_id, config={"displayModeBar": False}, **kwargs)),
        style=_CARD_STYLE,
    )


def _slider(id_, label, min_, max_, value, step=1, marks=None):
    if marks is None:
        marks = {min_: str(min_), max_: str(max_)}
    return html.Div([
        html.Label(label, style={"color": _TEXT, "fontSize": "0.8rem", "marginBottom": "2px"}),
        dcc.Slider(id=id_, min=min_, max=max_, value=value, step=step, marks=marks,
                   tooltip={"placement": "bottom", "always_visible": False}),
    ], style={"marginBottom": "0.75rem"})


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout = html.Div([
    # Header
    html.Div([
        html.Div("ADVANCED ANALYTICS", style={
            "fontSize": "0.7rem", "fontWeight": "700", "letterSpacing": "0.1em",
            "color": GRAY_500, "marginBottom": "0.2rem",
        }),
        html.H2("Time Series Analytics Suite", style={
            "fontSize": "1.6rem", "fontWeight": "700", "color": _TEXT, "margin": "0 0 0.75rem 0",
        }),
    ]),

    # Global product selector
    html.Div([
        html.Label("Primary Series", style={"color": _TEXT, "fontWeight": "600", "marginRight": "0.75rem"}),
        dcc.Dropdown(
            id="p15-product",
            options=_SERIES_OPTIONS,
            value=_DEFAULT_SERIES,
            clearable=False,
            style={"width": "350px", "backgroundColor": "#fff"},
        ),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"}),

    # Tabs
    dbc.Tabs([
        # ---- Tab 1: Regime Detection ----
        dbc.Tab(label="Regime Detection", tab_id="tab-regime", children=html.Div([
            _slider("p15-vol-window", "Volatility Window (weeks)", 4, 52, 20),
            dbc.Row([
                dbc.Col(_chart_card("p15-cusum"), lg=6),
                dbc.Col(_chart_card("p15-vol-regime"), lg=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(_chart_card("p15-structural-break"), lg=12),
            ]),
        ], style={"paddingTop": "1rem"})),

        # ---- Tab 2: Forecasting Arena ----
        dbc.Tab(label="Forecasting Arena", tab_id="tab-forecast", children=html.Div([
            dbc.Row([
                dbc.Col(_slider("p15-fc-horizon", "Forecast Horizon (weeks)", 4, 26, 12), lg=4),
                dbc.Col(_slider("p15-fc-holdout", "Holdout Period (weeks)", 8, 52, 26), lg=4),
            ]),
            dbc.Row([
                dbc.Col(_chart_card("p15-stl"), lg=6),
                dbc.Col(_chart_card("p15-forecast-compare"), lg=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Div(id="p15-forecast-metrics"), lg=12),
            ]),
        ], style={"paddingTop": "1rem"})),

        # ---- Tab 3: Cross-Product Dynamics ----
        dbc.Tab(label="Cross-Product Dynamics", tab_id="tab-cross", children=html.Div([
            html.Div([
                html.Label("Select Products", style={"color": _TEXT, "fontWeight": "600", "marginRight": "0.75rem"}),
                dcc.Dropdown(
                    id="p15-cross-products",
                    options=_SERIES_OPTIONS,
                    value=_CROSS_DEFAULTS,
                    multi=True,
                    style={"flex": "1", "backgroundColor": "#fff"},
                ),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "0.75rem"}),
            _slider("p15-corr-window", "Rolling Correlation Window (weeks)", 8, 104, 26),
            html.Div([
                html.Label("Lead-Lag Pair", style={"color": _TEXT, "fontWeight": "600", "marginRight": "0.75rem"}),
                dcc.Dropdown(id="p15-lag-series-a", options=_SERIES_OPTIONS, value="WCESTUS1",
                             clearable=False, style={"width": "240px", "marginRight": "0.5rem", "backgroundColor": "#fff"}),
                html.Span("vs", style={"color": _TEXT, "margin": "0 0.5rem"}),
                dcc.Dropdown(id="p15-lag-series-b", options=_SERIES_OPTIONS, value="WCRFPUS2",
                             clearable=False, style={"width": "240px", "backgroundColor": "#fff"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"}),
            dbc.Row([
                dbc.Col(_chart_card("p15-granger"), lg=6),
                dbc.Col(_chart_card("p15-rolling-corr"), lg=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(_chart_card("p15-pca"), lg=6),
                dbc.Col(_chart_card("p15-lead-lag"), lg=6),
            ]),
        ], style={"paddingTop": "1rem"})),

        # ---- Tab 4: Seasonal Intelligence ----
        dbc.Tab(label="Seasonal Intelligence", tab_id="tab-seasonal", children=html.Div([
            dbc.Row([
                dbc.Col(_chart_card("p15-stl-seasonal"), lg=6),
                dbc.Col(_chart_card("p15-calendar-heatmap"), lg=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(_chart_card("p15-seasonal-deviation"), lg=6),
                dbc.Col(_chart_card("p15-seasonal-strength"), lg=6),
            ]),
        ], style={"paddingTop": "1rem"})),

        # ---- Tab 5: Risk & Distribution ----
        dbc.Tab(label="Risk & Distribution", tab_id="tab-risk", children=html.Div([
            dbc.Row([
                dbc.Col(_slider("p15-bb-window", "Bollinger Window", 10, 52, 20), lg=4),
                dbc.Col(_slider("p15-bb-std", "Std Multiplier", 1, 3, 2), lg=4),
            ]),
            dbc.Row([
                dbc.Col(_chart_card("p15-drawdown"), lg=6),
                dbc.Col(_chart_card("p15-bollinger"), lg=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(_chart_card("p15-distribution"), lg=6),
                dbc.Col(_chart_card("p15-qq"), lg=6),
            ]),
        ], style={"paddingTop": "1rem"})),

    ], id="p15-tabs", active_tab="tab-regime",
       style={"backgroundColor": _BG}),

], style=_PAGE_STYLE)


# ===================================================================
# TAB 1: REGIME DETECTION CALLBACKS
# ===================================================================

@callback(Output("p15-cusum", "figure"), Input("p15-product", "value"))
def update_cusum(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 30:
        return _empty_fig("Insufficient data for CUSUM")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    changes = np.diff(vals)
    mean_chg = np.mean(changes)
    std_chg = np.std(changes)
    if std_chg == 0:
        return _empty_fig("Zero variance — cannot compute CUSUM")

    # CUSUM algorithm
    threshold = 4.0 * std_chg
    cusum_pos = np.zeros(len(changes))
    cusum_neg = np.zeros(len(changes))
    changepoints = []
    for i in range(1, len(changes)):
        cusum_pos[i] = max(0, cusum_pos[i - 1] + (changes[i] - mean_chg) - 0.5 * std_chg)
        cusum_neg[i] = max(0, cusum_neg[i - 1] - (changes[i] - mean_chg) - 0.5 * std_chg)
        if cusum_pos[i] > threshold or cusum_neg[i] > threshold:
            changepoints.append(i)
            cusum_pos[i] = 0
            cusum_neg[i] = 0

    fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4], vertical_spacing=0.08,
                        subplot_titles=[f"{name} with Detected Changepoints", "CUSUM Statistics"])

    cdates = dates[1:]  # diff reduces length by 1

    fig.add_trace(go.Scatter(x=pd.to_datetime(dates), y=vals, mode="lines",
                             name=name, line=dict(color=_ACCENT_COLORS[0], width=1.5)), row=1, col=1)

    for cp in changepoints:
        fig.add_vline(x=pd.to_datetime(cdates[cp]), line_width=1, line_dash="dash",
                      line_color="#ff6b6b", row=1, col=1)

    fig.add_trace(go.Scatter(x=pd.to_datetime(cdates), y=cusum_pos, mode="lines",
                             name="CUSUM+", line=dict(color=_ACCENT_COLORS[3], width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=pd.to_datetime(cdates), y=cusum_neg, mode="lines",
                             name="CUSUM-", line=dict(color=_ACCENT_COLORS[1], width=1)), row=2, col=1)
    fig.add_hline(y=threshold, line_dash="dot", line_color=_TEXT, line_width=0.8,
                  annotation_text="Threshold", row=2, col=1)

    _apply_theme(fig, 520)
    fig.update_layout(title=dict(text=f"CUSUM Changepoint Detection — {name}", font=dict(size=13)))
    return fig


@callback(Output("p15-vol-regime", "figure"),
          Input("p15-product", "value"), Input("p15-vol-window", "value"))
def update_vol_regime(series_id, window):
    dates, vals = _get_ts(series_id)
    if len(vals) < window + 10:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    s = pd.Series(vals)
    roll_std = s.rolling(window).std().values

    # Percentiles for background shading
    valid_std = roll_std[~np.isnan(roll_std)]
    if len(valid_std) < 2:
        return _empty_fig("Cannot compute volatility")
    p33 = np.percentile(valid_std, 33)
    p66 = np.percentile(valid_std, 66)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    dt = pd.to_datetime(dates)

    # Background shading by volatility regime
    for i in range(window, len(vals)):
        v = roll_std[i]
        if np.isnan(v):
            continue
        color = "rgba(107,203,119,0.12)" if v <= p33 else \
                "rgba(255,217,61,0.12)" if v <= p66 else "rgba(255,107,107,0.12)"
        fig.add_vrect(x0=dt[i - 1], x1=dt[i], fillcolor=color, line_width=0, layer="below")

    fig.add_trace(go.Scatter(x=dt, y=vals, mode="lines", name=name,
                             line=dict(color=_ACCENT_COLORS[0], width=1.5)), secondary_y=False)
    fig.add_trace(go.Scatter(x=dt, y=roll_std, mode="lines", name=f"Rolling Std ({window}w)",
                             line=dict(color=_ACCENT_COLORS[2], width=1, dash="dot")), secondary_y=True)

    _apply_theme(fig)
    fig.update_layout(title=dict(text=f"Volatility Regime Map — {name}", font=dict(size=13)))
    fig.update_yaxes(title_text=name, secondary_y=False)
    fig.update_yaxes(title_text="Volatility", secondary_y=True)
    return fig


@callback(Output("p15-structural-break", "figure"), Input("p15-product", "value"))
def update_structural_break(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 60:
        return _empty_fig("Insufficient data for structural break analysis")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    window = 26
    slopes = np.full(len(vals), np.nan)
    x = np.arange(window)
    for i in range(window, len(vals)):
        segment = vals[i - window:i]
        coeffs = np.polyfit(x, segment, 1)
        slopes[i] = coeffs[0]

    dt = pd.to_datetime(dates)

    fig = make_subplots(rows=2, cols=1, row_heights=[0.5, 0.5], vertical_spacing=0.08,
                        subplot_titles=[f"{name}", "Rolling 26-Week Slope"])

    fig.add_trace(go.Scatter(x=dt, y=vals, mode="lines", name=name,
                             line=dict(color=_ACCENT_COLORS[0], width=1.5)), row=1, col=1)
    colors = [_ACCENT_COLORS[3] if s >= 0 else _ACCENT_COLORS[1] if not np.isnan(s)
              else "rgba(0,0,0,0)" for s in slopes]
    fig.add_trace(go.Bar(x=dt, y=slopes, name="Slope", marker_color=colors, opacity=0.7), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color=_TEXT, line_width=0.5, row=2, col=1)

    _apply_theme(fig, 440)
    fig.update_layout(title=dict(text=f"Structural Break Analysis — {name}", font=dict(size=13)),
                      showlegend=False)
    return fig


# ===================================================================
# TAB 2: FORECASTING ARENA CALLBACKS
# ===================================================================

@callback(Output("p15-stl", "figure"), Input("p15-product", "value"))
def update_stl(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 104:
        return _empty_fig("Need 2+ years for STL decomposition")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    try:
        from statsmodels.tsa.seasonal import STL
        s = pd.Series(vals, index=pd.to_datetime(dates))
        result = STL(s, period=52, robust=True).fit()
    except Exception as e:
        return _empty_fig(f"STL error: {e}")

    dt = pd.to_datetime(dates)
    fig = make_subplots(rows=4, cols=1, row_heights=[0.3, 0.3, 0.2, 0.2], vertical_spacing=0.04,
                        subplot_titles=["Observed", "Trend", "Seasonal", "Residual"])

    fig.add_trace(go.Scatter(x=dt, y=result.observed, mode="lines",
                             line=dict(color=_ACCENT_COLORS[0], width=1), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=dt, y=result.trend, mode="lines",
                             line=dict(color=_ACCENT_COLORS[2], width=2), showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=dt, y=result.seasonal, mode="lines",
                             line=dict(color=_ACCENT_COLORS[3], width=1), showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=dt, y=result.resid, mode="lines",
                             line=dict(color=_ACCENT_COLORS[1], width=1), showlegend=False), row=4, col=1)

    _apply_theme(fig, 580)
    fig.update_layout(title=dict(text=f"STL Decomposition — {name}", font=dict(size=13)))
    return fig


@callback(
    Output("p15-forecast-compare", "figure"),
    Output("p15-forecast-metrics", "children"),
    Input("p15-product", "value"),
    Input("p15-fc-horizon", "value"),
    Input("p15-fc-holdout", "value"),
)
def update_forecast(series_id, horizon, holdout):
    dates, vals = _get_ts(series_id)
    if len(vals) < 104 + holdout:
        return _empty_fig("Insufficient data for forecasting"), html.Div()

    name = ANALYTICS_SERIES.get(series_id, series_id)
    n = len(vals)
    split = n - holdout
    train_vals = vals[:split]
    test_vals = vals[split:split + horizon]
    test_dates = dates[split:split + horizon]
    train_dates = dates[:split]
    actual_horizon = len(test_vals)
    if actual_horizon < 2:
        return _empty_fig("Holdout too large"), html.Div()

    dt_train = pd.to_datetime(train_dates)
    dt_test = pd.to_datetime(test_dates)

    fig = go.Figure()
    # Show last 104 weeks of training data
    show_from = max(0, split - 104)
    fig.add_trace(go.Scatter(x=pd.to_datetime(dates[show_from:split]), y=vals[show_from:split],
                             mode="lines", name="Training", line=dict(color=_ACCENT_COLORS[0], width=1.5)))
    fig.add_trace(go.Scatter(x=dt_test, y=test_vals, mode="lines+markers",
                             name="Actual (Holdout)", line=dict(color=_TEXT, width=2),
                             marker=dict(size=4)))

    metrics_rows = []

    # --- Naive seasonal (same week last year) ---
    naive_fc = vals[split - 52:split - 52 + actual_horizon] if split >= 52 else None
    if naive_fc is not None and len(naive_fc) == actual_horizon:
        fig.add_trace(go.Scatter(x=dt_test, y=naive_fc, mode="lines",
                                 name="Naive Seasonal", line=dict(color=_ACCENT_COLORS[2], width=1.5, dash="dot")))
        err = test_vals - naive_fc
        metrics_rows.append(("Naive Seasonal",
                             f"{np.mean(np.abs(err)):.1f}",
                             f"{np.sqrt(np.mean(err**2)):.1f}",
                             f"{np.mean(np.abs(err / test_vals)) * 100:.2f}%"))

    # --- Holt-Winters ---
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        hw = ExponentialSmoothing(train_vals, seasonal_periods=52, trend="add",
                                  seasonal="add", use_boxcox=False).fit(optimized=True)
        hw_fc = hw.forecast(actual_horizon)
        fig.add_trace(go.Scatter(x=dt_test, y=hw_fc, mode="lines",
                                 name="Holt-Winters", line=dict(color=_ACCENT_COLORS[3], width=1.5, dash="dash")))
        err = test_vals - hw_fc
        metrics_rows.append(("Holt-Winters",
                             f"{np.mean(np.abs(err)):.1f}",
                             f"{np.sqrt(np.mean(err**2)):.1f}",
                             f"{np.mean(np.abs(err / test_vals)) * 100:.2f}%"))
    except Exception:
        pass

    # --- SARIMAX ---
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        model = SARIMAX(train_vals, order=(1, 1, 1), seasonal_order=(1, 1, 0, 52),
                        enforce_stationarity=False, enforce_invertibility=False)
        fit = model.fit(disp=False, maxiter=50)
        pred = fit.get_forecast(actual_horizon)
        sarima_fc = pred.predicted_mean
        ci = pred.conf_int(alpha=0.05)
        fig.add_trace(go.Scatter(x=dt_test, y=sarima_fc, mode="lines",
                                 name="SARIMAX", line=dict(color=_ACCENT_COLORS[1], width=2)))
        fig.add_trace(go.Scatter(x=dt_test, y=ci[:, 1], mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dt_test, y=ci[:, 0], mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(255,107,107,0.15)",
                                 name="95% CI", hoverinfo="skip"))
        err = test_vals - sarima_fc
        metrics_rows.append(("SARIMAX(1,1,1)(1,1,0,52)",
                             f"{np.mean(np.abs(err)):.1f}",
                             f"{np.sqrt(np.mean(err**2)):.1f}",
                             f"{np.mean(np.abs(err / test_vals)) * 100:.2f}%"))
    except Exception:
        # Fallback to non-seasonal ARIMA
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            model = SARIMAX(train_vals, order=(1, 1, 1), enforce_stationarity=False, enforce_invertibility=False)
            fit = model.fit(disp=False, maxiter=50)
            pred = fit.get_forecast(actual_horizon)
            arima_fc = pred.predicted_mean
            fig.add_trace(go.Scatter(x=dt_test, y=arima_fc, mode="lines",
                                     name="ARIMA(1,1,1)", line=dict(color=_ACCENT_COLORS[1], width=2)))
            err = test_vals - arima_fc
            metrics_rows.append(("ARIMA(1,1,1)",
                                 f"{np.mean(np.abs(err)):.1f}",
                                 f"{np.sqrt(np.mean(err**2)):.1f}",
                                 f"{np.mean(np.abs(err / test_vals)) * 100:.2f}%"))
        except Exception:
            pass

    _apply_theme(fig)
    fig.update_layout(title=dict(text=f"Forecast Comparison — {name}", font=dict(size=13)))

    # Build metrics table
    if metrics_rows:
        table = dbc.Table(
            [html.Thead(html.Tr([html.Th(h, style={"color": _TEXT}) for h in ["Method", "MAE", "RMSE", "MAPE"]]))] +
            [html.Tbody([html.Tr([html.Td(c, style={"color": _TEXT}) for c in row]) for row in metrics_rows])],
            bordered=True, hover=True,
            style={"backgroundColor": _BG2, "marginTop": "0.5rem", "color": _TEXT},
        )
    else:
        table = html.Div("No forecast models converged.", style={"color": _TEXT})

    return fig, table


# ===================================================================
# TAB 3: CROSS-PRODUCT DYNAMICS CALLBACKS
# ===================================================================

@callback(Output("p15-granger", "figure"), Input("p15-cross-products", "value"))
def update_granger(selected):
    if not selected or len(selected) < 2:
        return _empty_fig("Select at least 2 products")
    selected = selected[:8]  # cap for performance

    from statsmodels.tsa.stattools import grangercausalitytests

    names = [ANALYTICS_SERIES.get(s, s) for s in selected]
    short = [n[:12] for n in names]
    n = len(selected)
    pvals = np.ones((n, n))

    # Get aligned data
    cols = [s for s in selected if s in _pivot.columns]
    if len(cols) < 2:
        return _empty_fig("Series not found in data")

    df = _pivot[["period"] + cols].dropna()
    if len(df) < 30:
        return _empty_fig("Insufficient overlapping data")

    # Use weekly changes for stationarity
    changes = df[cols].diff().dropna()

    for i in range(n):
        for j in range(n):
            if i == j or selected[i] not in changes.columns or selected[j] not in changes.columns:
                continue
            try:
                data = changes[[selected[j], selected[i]]].values  # does i Granger-cause j?
                result = grangercausalitytests(data, maxlag=4, verbose=False)
                min_p = min(result[lag][0]["ssr_ftest"][1] for lag in result)
                pvals[i, j] = min_p
            except Exception:
                pvals[i, j] = 1.0

    fig = go.Figure(go.Heatmap(
        z=pvals, x=short, y=short,
        colorscale=[[0, "#ff6b6b"], [0.05, "#ffd93d"], [0.1, "#2a2a4a"], [1, "#1a1a2e"]],
        zmin=0, zmax=0.2,
        text=np.round(pvals, 3), texttemplate="%{text:.3f}",
        textfont=dict(size=9, color=_TEXT),
        colorbar=dict(title=dict(text="p-value", font=dict(color=_TEXT)), tickfont=dict(color=_TEXT)),
    ))

    _apply_theme(fig)
    fig.update_layout(
        title=dict(text="Granger Causality (rows cause columns)", font=dict(size=13)),
        xaxis=dict(title="Effect", tickangle=45),
        yaxis=dict(title="Cause"),
    )
    return fig


@callback(Output("p15-rolling-corr", "figure"),
          Input("p15-cross-products", "value"), Input("p15-corr-window", "value"))
def update_rolling_corr(selected, window):
    if not selected or len(selected) < 2:
        return _empty_fig("Select at least 2 products")

    cols = [s for s in selected if s in _pivot.columns][:6]
    df = _pivot[["period"] + cols].dropna()
    if len(df) < window + 10:
        return _empty_fig("Insufficient data")

    fig = go.Figure()
    color_idx = 0
    # Show pairwise correlations for first few pairs
    for i in range(len(cols)):
        for j in range(i + 1, min(len(cols), i + 3)):
            corr = df[cols[i]].rolling(window).corr(df[cols[j]])
            n1 = ANALYTICS_SERIES.get(cols[i], cols[i])[:10]
            n2 = ANALYTICS_SERIES.get(cols[j], cols[j])[:10]
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df["period"]), y=corr, mode="lines",
                name=f"{n1} / {n2}",
                line=dict(color=_ACCENT_COLORS[color_idx % len(_ACCENT_COLORS)], width=1.5),
            ))
            color_idx += 1

    fig.add_hline(y=0, line_dash="dot", line_color=_TEXT, line_width=0.5)
    _apply_theme(fig)
    fig.update_layout(
        title=dict(text=f"Rolling {window}-Week Correlation", font=dict(size=13)),
        yaxis=dict(title="Correlation", range=[-1, 1]),
    )
    return fig


@callback(Output("p15-pca", "figure"), Input("p15-cross-products", "value"))
def update_pca(selected):
    if not selected or len(selected) < 3:
        return _empty_fig("Select at least 3 products for PCA")

    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    cols = [s for s in selected if s in _pivot.columns]
    df = _pivot[cols].dropna()
    if len(df) < 30:
        return _empty_fig("Insufficient data")

    # Use weekly changes
    changes = df.diff().dropna()
    scaled = StandardScaler().fit_transform(changes)

    pca = PCA()
    pca.fit(scaled)

    fig = make_subplots(rows=1, cols=2, subplot_titles=["Variance Explained", "PC1 vs PC2 Loadings"],
                        column_widths=[0.4, 0.6])

    var_exp = pca.explained_variance_ratio_
    fig.add_trace(go.Bar(
        x=[f"PC{i+1}" for i in range(len(var_exp))],
        y=var_exp,
        marker_color=_ACCENT_COLORS[0], opacity=0.8, showlegend=False,
    ), row=1, col=1)

    # Biplot of loadings
    loadings = pca.components_[:2]
    short_names = [ANALYTICS_SERIES.get(c, c)[:14] for c in cols]
    for i, name in enumerate(short_names):
        fig.add_trace(go.Scatter(
            x=[0, loadings[0, i]], y=[0, loadings[1, i]],
            mode="lines+text", text=["", name], textposition="top center",
            textfont=dict(size=9, color=_ACCENT_COLORS[i % len(_ACCENT_COLORS)]),
            line=dict(color=_ACCENT_COLORS[i % len(_ACCENT_COLORS)], width=2),
            showlegend=False,
        ), row=1, col=2)

    _apply_theme(fig)
    fig.update_layout(title=dict(text="PCA — Weekly Changes", font=dict(size=13)))
    fig.update_yaxes(title_text="Variance Ratio", row=1, col=1)
    fig.update_xaxes(title_text="PC1 Loading", row=1, col=2)
    fig.update_yaxes(title_text="PC2 Loading", row=1, col=2)
    return fig


@callback(Output("p15-lead-lag", "figure"),
          Input("p15-lag-series-a", "value"), Input("p15-lag-series-b", "value"))
def update_lead_lag(series_a, series_b):
    _, vals_a = _get_ts(series_a)
    _, vals_b = _get_ts(series_b)
    min_len = min(len(vals_a), len(vals_b))
    if min_len < 60:
        return _empty_fig("Insufficient data for cross-correlation")

    a = vals_a[-min_len:]
    b = vals_b[-min_len:]
    # Standardize
    a = (a - np.mean(a)) / np.std(a)
    b = (b - np.mean(b)) / np.std(b)

    max_lag = 26
    lags = np.arange(-max_lag, max_lag + 1)
    ccf = np.array([np.corrcoef(a[max_lag:min_len - max_lag], b[max_lag + l:min_len - max_lag + l])[0, 1]
                     for l in lags])

    peak_lag = lags[np.argmax(np.abs(ccf))]
    peak_val = ccf[np.argmax(np.abs(ccf))]

    colors = [_ACCENT_COLORS[1] if abs(c) == abs(peak_val) else _ACCENT_COLORS[0] for c in ccf]

    name_a = ANALYTICS_SERIES.get(series_a, series_a)[:18]
    name_b = ANALYTICS_SERIES.get(series_b, series_b)[:18]

    fig = go.Figure(go.Bar(x=lags, y=ccf, marker_color=colors, opacity=0.8))
    fig.add_hline(y=0, line_dash="dot", line_color=_TEXT, line_width=0.5)

    # Significance bounds
    sig = 1.96 / np.sqrt(min_len)
    fig.add_hline(y=sig, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=0.5)
    fig.add_hline(y=-sig, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=0.5)

    fig.add_annotation(x=peak_lag, y=peak_val, text=f"Peak: lag={peak_lag}, r={peak_val:.3f}",
                       showarrow=True, arrowhead=2, arrowcolor=_TEXT, font=dict(color=_TEXT, size=10))

    _apply_theme(fig)
    fig.update_layout(
        title=dict(text=f"Cross-Correlation: {name_a} vs {name_b}", font=dict(size=13)),
        xaxis=dict(title="Lag (weeks) — negative = A leads"),
        yaxis=dict(title="Correlation"),
    )
    return fig


# ===================================================================
# TAB 4: SEASONAL INTELLIGENCE CALLBACKS
# ===================================================================

@callback(Output("p15-stl-seasonal", "figure"), Input("p15-product", "value"))
def update_stl_seasonal(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 104:
        return _empty_fig("Need 2+ years for seasonal extraction")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    try:
        from statsmodels.tsa.seasonal import STL
        s = pd.Series(vals, index=pd.to_datetime(dates))
        result = STL(s, period=52, robust=True).fit()
    except Exception as e:
        return _empty_fig(f"STL error: {e}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pd.to_datetime(dates), y=result.seasonal, mode="lines",
                             name="Seasonal Component", line=dict(color=_ACCENT_COLORS[3], width=1.5)))
    fig.add_hline(y=0, line_dash="dot", line_color=_TEXT, line_width=0.5)

    _apply_theme(fig)
    fig.update_layout(title=dict(text=f"STL Seasonal Component — {name}", font=dict(size=13)),
                      yaxis=dict(title="Seasonal Effect"))
    return fig


@callback(Output("p15-calendar-heatmap", "figure"), Input("p15-product", "value"))
def update_calendar_heatmap(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 52:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    df = pd.DataFrame({"date": pd.to_datetime(dates), "value": vals})
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year"] = df["date"].dt.year

    pivot = df.pivot_table(values="value", index="year", columns="week", aggfunc="mean")

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=[str(w) for w in pivot.columns], y=[str(y) for y in pivot.index],
        colorscale=COLORSCALE_SEQUENTIAL,
        colorbar=dict(title=dict(text="Value", font=dict(color=_TEXT)), tickfont=dict(color=_TEXT)),
        hoverongaps=False,
    ))

    _apply_theme(fig, 420)
    fig.update_layout(
        title=dict(text=f"Calendar Heatmap — {name}", font=dict(size=13)),
        xaxis=dict(title="Week of Year", dtick=4),
        yaxis=dict(title="Year"),
    )
    return fig


@callback(Output("p15-seasonal-deviation", "figure"), Input("p15-product", "value"))
def update_seasonal_deviation(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 52:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    df = pd.DataFrame({"date": pd.to_datetime(dates), "value": vals})
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year"] = df["date"].dt.year

    current_year = df["year"].max()
    # 5-year average
    hist_years = range(current_year - 5, current_year)
    hist = df[df["year"].isin(hist_years)]
    stats = hist.groupby("week")["value"].agg(["mean", "min", "max"]).reset_index()

    cur = df[df["year"] == current_year].sort_values("week")

    fig = go.Figure()
    # Range band
    fig.add_trace(go.Scatter(x=stats["week"], y=stats["max"], mode="lines", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=stats["week"], y=stats["min"], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(0,212,255,0.12)",
                             name="5-Year Range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=stats["week"], y=stats["mean"], mode="lines",
                             line=dict(color="rgba(255,255,255,0.4)", width=1.5, dash="dash"),
                             name="5-Year Avg"))
    # Prior year
    prior = df[df["year"] == current_year - 1].sort_values("week")
    if not prior.empty:
        fig.add_trace(go.Scatter(x=prior["week"], y=prior["value"], mode="lines",
                                 name=str(current_year - 1), line=dict(color=_ACCENT_COLORS[2], width=1.5)))
    # Current year
    if not cur.empty:
        fig.add_trace(go.Scatter(x=cur["week"], y=cur["value"], mode="lines",
                                 name=str(current_year), line=dict(color=_ACCENT_COLORS[0], width=2.5)))

    _apply_theme(fig)
    fig.update_layout(
        title=dict(text=f"Seasonal Deviation — {name}", font=dict(size=13)),
        xaxis=dict(title="Week of Year"),
        yaxis=dict(title="Value"),
    )
    return fig


@callback(Output("p15-seasonal-strength", "figure"), Input("p15-product", "value"))
def update_seasonal_strength(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 104:
        return _empty_fig("Need 2+ years for seasonal strength")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    df = pd.DataFrame({"date": pd.to_datetime(dates), "value": vals})
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year"] = df["date"].dt.year

    years = sorted(df["year"].unique())
    strengths = []
    for yr in years:
        yr_data = df[df["year"] == yr]["value"]
        if len(yr_data) < 20:
            continue
        total_var = yr_data.var()
        if total_var == 0:
            strengths.append({"year": yr, "strength": 0, "amplitude": 0})
            continue
        # Seasonal variance: variance of weekly means
        wk_means = df[df["year"] == yr].groupby("week")["value"].mean()
        seasonal_var = wk_means.var()
        strengths.append({
            "year": yr,
            "strength": seasonal_var / total_var if total_var > 0 else 0,
            "amplitude": wk_means.max() - wk_means.min(),
        })

    if not strengths:
        return _empty_fig("No data")

    sdf = pd.DataFrame(strengths)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=sdf["year"].astype(str), y=sdf["strength"], name="Seasonal Variance Ratio",
                         marker_color=_ACCENT_COLORS[0], opacity=0.8), secondary_y=False)
    fig.add_trace(go.Scatter(x=sdf["year"].astype(str), y=sdf["amplitude"], mode="lines+markers",
                             name="Amplitude (Max-Min)", line=dict(color=_ACCENT_COLORS[1], width=2),
                             marker=dict(size=6)), secondary_y=True)

    _apply_theme(fig)
    fig.update_layout(title=dict(text=f"Seasonal Strength by Year — {name}", font=dict(size=13)))
    fig.update_yaxes(title_text="Variance Ratio", secondary_y=False)
    fig.update_yaxes(title_text="Amplitude", secondary_y=True)
    return fig


# ===================================================================
# TAB 5: RISK & DISTRIBUTION CALLBACKS
# ===================================================================

@callback(Output("p15-drawdown", "figure"), Input("p15-product", "value"))
def update_drawdown(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 30:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    dt = pd.to_datetime(dates)

    # Running max and drawdown
    running_max = np.maximum.accumulate(vals)
    drawdown = (vals - running_max) / running_max * 100

    fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4], vertical_spacing=0.08,
                        subplot_titles=[f"{name} with Peak-to-Trough", "Drawdown %"])

    fig.add_trace(go.Scatter(x=dt, y=vals, mode="lines", name=name,
                             line=dict(color=_ACCENT_COLORS[0], width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=dt, y=running_max, mode="lines", name="Running Max",
                             line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot")), row=1, col=1)

    # Find top 3 drawdowns
    in_drawdown = False
    dd_events = []
    start_idx = 0
    for i in range(len(drawdown)):
        if drawdown[i] < -0.5 and not in_drawdown:
            in_drawdown = True
            start_idx = i
        elif (drawdown[i] >= 0 or i == len(drawdown) - 1) and in_drawdown:
            in_drawdown = False
            trough_idx = start_idx + np.argmin(drawdown[start_idx:i + 1])
            dd_events.append((start_idx, trough_idx, i, drawdown[trough_idx]))

    dd_events.sort(key=lambda x: x[3])
    shade_colors = ["rgba(255,107,107,0.2)", "rgba(255,217,61,0.15)", "rgba(192,132,252,0.12)"]
    for rank, ev in enumerate(dd_events[:3]):
        fig.add_vrect(x0=dt[ev[0]], x1=dt[ev[2]], fillcolor=shade_colors[rank],
                      line_width=0, row=1, col=1)

    fig.add_trace(go.Scatter(x=dt, y=drawdown, mode="lines", name="Drawdown %",
                             fill="tozeroy", fillcolor="rgba(255,107,107,0.2)",
                             line=dict(color=_ACCENT_COLORS[1], width=1)), row=2, col=1)

    max_dd = np.min(drawdown)
    max_dd_idx = np.argmin(drawdown)
    fig.add_annotation(x=dt[max_dd_idx], y=max_dd, text=f"Max: {max_dd:.1f}%",
                       showarrow=True, arrowhead=2, arrowcolor=_TEXT,
                       font=dict(color=_TEXT, size=10), row=2, col=1)

    _apply_theme(fig, 520)
    fig.update_layout(title=dict(text=f"Drawdown Analysis — {name}", font=dict(size=13)))
    return fig


@callback(Output("p15-bollinger", "figure"),
          Input("p15-product", "value"), Input("p15-bb-window", "value"), Input("p15-bb-std", "value"))
def update_bollinger(series_id, window, std_mult):
    dates, vals = _get_ts(series_id)
    if len(vals) < window + 10:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    s = pd.Series(vals)
    sma = s.rolling(window).mean()
    std = s.rolling(window).std()
    upper = sma + std_mult * std
    lower = sma - std_mult * std
    bandwidth = ((upper - lower) / sma * 100).values

    # Squeeze detection: bandwidth in bottom 10th percentile
    valid_bw = bandwidth[~np.isnan(bandwidth)]
    if len(valid_bw) < 5:
        return _empty_fig("Cannot compute Bollinger Bands")
    squeeze_threshold = np.percentile(valid_bw, 10)

    dt = pd.to_datetime(dates)

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], vertical_spacing=0.08,
                        subplot_titles=[f"{name} with Bollinger Bands", "Bandwidth %"])

    # Squeeze shading
    for i in range(window, len(vals)):
        if not np.isnan(bandwidth[i]) and bandwidth[i] <= squeeze_threshold:
            fig.add_vrect(x0=dt[i - 1], x1=dt[i], fillcolor="rgba(255,217,61,0.15)",
                          line_width=0, row=1, col=1)

    fig.add_trace(go.Scatter(x=dt, y=upper.values, mode="lines", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=dt, y=lower.values, mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(0,212,255,0.08)",
                             name="Bollinger Band", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=dt, y=sma.values, mode="lines", name=f"SMA({window})",
                             line=dict(color="rgba(255,255,255,0.5)", width=1, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=dt, y=vals, mode="lines", name=name,
                             line=dict(color=_ACCENT_COLORS[0], width=1.5)), row=1, col=1)

    fig.add_trace(go.Scatter(x=dt, y=bandwidth, mode="lines", name="Bandwidth %",
                             line=dict(color=_ACCENT_COLORS[4], width=1)), row=2, col=1)
    fig.add_hline(y=squeeze_threshold, line_dash="dot", line_color=_ACCENT_COLORS[2],
                  line_width=0.8, row=2, col=1,
                  annotation_text="Squeeze", annotation_font_color=_TEXT)

    _apply_theme(fig, 520)
    fig.update_layout(title=dict(text=f"Bollinger Bands & Squeeze — {name}", font=dict(size=13)))
    return fig


@callback(Output("p15-distribution", "figure"), Input("p15-product", "value"))
def update_distribution(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 30:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    changes = np.diff(vals)
    changes = changes[~np.isnan(changes)]
    if len(changes) < 10:
        return _empty_fig("Insufficient changes data")

    from scipy import stats as sp_stats
    from statsmodels.stats.stattools import jarque_bera

    skew = sp_stats.skew(changes)
    kurt = sp_stats.kurtosis(changes)
    jb_stat, jb_pval, _, _ = jarque_bera(changes)

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=changes, nbinsx=40, name="Weekly Changes",
        marker_color=_ACCENT_COLORS[0], opacity=0.7,
        histnorm="probability density",
    ))

    # Fitted normal
    x_range = np.linspace(changes.min(), changes.max(), 200)
    normal_pdf = sp_stats.norm.pdf(x_range, np.mean(changes), np.std(changes))
    fig.add_trace(go.Scatter(x=x_range, y=normal_pdf, mode="lines", name="Normal Fit",
                             line=dict(color=_ACCENT_COLORS[1], width=2)))

    fig.add_annotation(
        text=f"Skewness: {skew:.3f}<br>Kurtosis: {kurt:.3f}<br>JB stat: {jb_stat:.1f} (p={jb_pval:.4f})",
        xref="paper", yref="paper", x=0.98, y=0.95, showarrow=False,
        font=dict(color=_TEXT, size=10), align="right",
        bgcolor="rgba(26,26,46,0.8)", bordercolor=_GRID, borderwidth=1,
    )

    _apply_theme(fig)
    fig.update_layout(
        title=dict(text=f"Weekly Change Distribution — {name}", font=dict(size=13)),
        xaxis=dict(title="Weekly Change"),
        yaxis=dict(title="Density"),
        barmode="overlay",
    )
    return fig


@callback(Output("p15-qq", "figure"), Input("p15-product", "value"))
def update_qq(series_id):
    dates, vals = _get_ts(series_id)
    if len(vals) < 30:
        return _empty_fig("Insufficient data")

    name = ANALYTICS_SERIES.get(series_id, series_id)
    changes = np.diff(vals)
    changes = changes[~np.isnan(changes)]
    if len(changes) < 10:
        return _empty_fig("Insufficient data")

    from scipy import stats as sp_stats
    sorted_changes = np.sort(changes)
    n = len(sorted_changes)
    theoretical = sp_stats.norm.ppf(np.arange(1, n + 1) / (n + 1))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=theoretical, y=sorted_changes, mode="markers",
                             name="Sample Quantiles",
                             marker=dict(color=_ACCENT_COLORS[0], size=4, opacity=0.7)))

    # Reference line
    slope, intercept = np.polyfit(theoretical, sorted_changes, 1)
    ref_line = slope * theoretical + intercept
    fig.add_trace(go.Scatter(x=theoretical, y=ref_line, mode="lines",
                             name="Reference Line",
                             line=dict(color=_ACCENT_COLORS[1], width=2, dash="dash")))

    _apply_theme(fig)
    fig.update_layout(
        title=dict(text=f"QQ Plot — {name} Weekly Changes", font=dict(size=13)),
        xaxis=dict(title="Theoretical Quantiles (Normal)"),
        yaxis=dict(title="Sample Quantiles"),
    )
    return fig
