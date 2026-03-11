import pandas as pd
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from src.utils.data_loader import loader
from src.utils.colors import (
    RED, ORANGE, BLUE, GREEN, PURPLE,
    POSITIVE, NEGATIVE, GRAY_50, GRAY_500, GRAY_800,
)

# ── Data ──────────────────────────────────────────────────────────────
METRICS = [
    ("WCESTUS1", "Crude Stocks",      "M bbl", 1000, ORANGE),
    ("WGTSTUS1", "Gasoline Stocks",   "M bbl", 1000, BLUE),
    ("WDISTUS1", "Distillate Stocks", "M bbl", 1000, GREEN),
    ("WKJSTUS1", "Jet Fuel Stocks",   "M bbl", 1000, PURPLE),
    ("WCRFPUS2", "Crude Production",  "kb/d",  1,    RED),
    ("WPULEUS3", "Refinery Util",     "%",     1,    GRAY_800),
]

SPARKLINES = [
    ("WCESTUS1", "Crude Oil Stocks",  ORANGE),
    ("WGTSTUS1", "Gasoline Stocks",   BLUE),
    ("WDISTUS1", "Distillate Stocks", GREEN),
]


def _load_data():
    try:
        df = loader.load_wps_pivot_data()
        df = df.sort_values("period")
        return df
    except Exception:
        return None


def _fmt(val, unit, divisor):
    v = val / divisor if divisor != 1 else val
    if unit == "%":
        return f"{v:.1f}%"
    if unit == "kb/d":
        return f"{v:,.0f}"
    return f"{v:.1f}M"


def _delta_str(delta, unit, divisor):
    d = delta / divisor if divisor != 1 else delta
    sign = "+" if d >= 0 else ""
    if unit == "%":
        return f"{sign}{d:.1f}%"
    if unit == "kb/d":
        return f"{sign}{d:,.0f}"
    return f"{sign}{d:.1f}M"


def create_metric_card(label, value_str, delta_str, delta_val, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, style={
                "fontSize": "0.7rem", "color": GRAY_500,
                "fontWeight": "700", "letterSpacing": "0.08em",
                "textTransform": "uppercase", "marginBottom": "0.4rem",
            }),
            html.Div(value_str, style={
                "fontSize": "1.6rem", "color": GRAY_800,
                "fontWeight": "700", "lineHeight": "1",
                "fontFeatureSettings": "'tnum' on",
                "marginBottom": "0.35rem",
            }),
            html.Div([
                html.Span(delta_str, style={
                    "color": POSITIVE if delta_val >= 0 else NEGATIVE,
                    "fontWeight": "600", "fontSize": "0.85rem",
                }),
                html.Span(" vs prev wk", style={
                    "color": GRAY_500, "fontSize": "0.8rem", "marginLeft": "4px",
                }),
            ]),
        ], style={"padding": "0.9rem 1rem"}),
        style={
            "borderTop": f"4px solid {color}",
            "borderLeft": "none", "borderRight": "none", "borderBottom": "none",
            "borderRadius": "0 0 10px 10px",
            "backgroundColor": "white",
            "boxShadow": "0 1px 8px rgba(0,0,0,0.06)",
            "height": "108px",
        },
        className="homepage-metric-card",
    )


def _build_sparkline(df, ticker, label, color):
    recent = df.tail(52)
    x = recent["period"]
    y = recent[ticker]
    last_val = y.iloc[-1]

    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fill_rgba = f"rgba({r},{g},{b},0.07)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=fill_rgba,
        showlegend=False, hovertemplate="%{x|%b %d}: %{y:,.0f}<extra></extra>",
    ))
    fig.add_annotation(
        x=x.iloc[-1], y=last_val,
        text=f"{last_val / 1000:.1f}M",
        showarrow=False, font=dict(size=11, color=color, weight=700),
        xanchor="left", xshift=6,
    )

    y_min, y_max = y.min(), y.max()
    pad = (y_max - y_min) * 0.08
    fig.update_layout(
        height=90, margin=dict(l=10, r=50, t=5, b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                   range=[y_min - pad, y_max + pad]),
        hovermode="x unified",
    )

    from dash import dcc
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, style={
                "fontSize": "0.8rem", "fontWeight": "600",
                "color": GRAY_800, "marginBottom": "0.25rem",
            }),
            dcc.Graph(figure=fig, config={"displayModeBar": False},
                      style={"height": "90px"}),
        ], style={"padding": "0.75rem 1rem"}),
        style={
            "border": "none", "borderRadius": "10px",
            "backgroundColor": "white",
            "boxShadow": "0 1px 8px rgba(0,0,0,0.06)",
        },
    )


# ── Build layout ──────────────────────────────────────────────────────
_df = _load_data()

if _df is not None and len(_df) >= 2:
    _latest = _df.iloc[-1]
    _prev = _df.iloc[-2]
    _last_date = _latest["period"].strftime("%B %d, %Y")

    _metric_cols = []
    for ticker, label, unit, divisor, color in METRICS:
        cur = _latest.get(ticker, 0)
        prv = _prev.get(ticker, 0)
        delta = cur - prv
        _metric_cols.append(
            dbc.Col(
                create_metric_card(label, _fmt(cur, unit, divisor),
                                   _delta_str(delta, unit, divisor), delta, color),
                lg=2, md=4, sm=6, className="mb-3",
            )
        )

    _sparkline_cols = []
    for ticker, label, color in SPARKLINES:
        _sparkline_cols.append(
            dbc.Col(_build_sparkline(_df, ticker, label, color),
                    lg=4, md=6, className="mb-3")
        )
else:
    _last_date = "--"
    _metric_cols = [dbc.Col(html.Div("Data unavailable"), lg=12)]
    _sparkline_cols = []

layout = html.Div([
    # Header strip
    dbc.Row([
        dbc.Col(
            html.Div("Market Summary", style={
                "fontSize": "1.1rem", "fontWeight": "600", "color": GRAY_800,
            }),
            width="auto",
        ),
        dbc.Col(
            html.Div([
                html.Span("EIA Weekly Petroleum Status Report", style={
                    "fontSize": "0.85rem", "color": GRAY_500,
                }),
                html.Span(" | ", style={"margin": "0 0.5rem", "color": "#dee2e6"}),
                html.Span(f"Last Updated: {_last_date}", style={
                    "fontSize": "0.85rem", "color": GRAY_500,
                }),
            ], style={"textAlign": "right"}),
        ),
    ], align="center", className="mb-4",
       style={"borderBottom": "1px solid #dee2e6", "paddingBottom": "0.75rem"}),

    # Metric cards
    dbc.Row(_metric_cols, className="mb-4"),

    # Sparklines
    dbc.Row(_sparkline_cols, className="mb-4"),

    # Footer
    html.Div(
        f"Data sourced from EIA Weekly Petroleum Status Report  |  Report date: {_last_date}",
        style={
            "textAlign": "center", "fontSize": "0.8rem",
            "color": GRAY_500, "padding": "1rem 0",
        },
    ),
], style={"padding": "1.5rem 2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"})
