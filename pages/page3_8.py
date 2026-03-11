"""DUC Analysis — comprehensive DUC (Drilled but Uncompleted) well analytics."""

from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from src.utils.data_loader import loader
from src.utils.colors import (
    RED, BLUE, GREEN, ORANGE, PURPLE, BLACK,
    POSITIVE, NEGATIVE, CHART_SEQUENCE, COLORSCALE_HEATMAP,
    GRAY_50, GRAY_200, GRAY_300, GRAY_500, GRAY_800, WHITE,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_STYLE = {"padding": "2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"}
CHART_HEIGHT = 440

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

REGIONS = ['Permian', 'Bakken', 'Eagle Ford', 'Appalachia', 'Haynesville', 'Rest of L48 ex GOM']

REGION_ABBREV = {
    'Permian': 'PM', 'Bakken': 'BK', 'Eagle Ford': 'EF',
    'Appalachia': 'AP', 'Haynesville': 'HA', 'Rest of L48 ex GOM': 'R48',
}

REGION_COLORS = {
    'Permian': RED, 'Bakken': BLUE, 'Eagle Ford': ORANGE,
    'Appalachia': GREEN, 'Haynesville': PURPLE, 'Rest of L48 ex GOM': GRAY_300,
}

REGION_SHORT = {
    'Permian': 'Permian', 'Bakken': 'Bakken', 'Eagle Ford': 'Eagle Ford',
    'Appalachia': 'Appalachia', 'Haynesville': 'Haynesville', 'Rest of L48 ex GOM': 'Rest of L48',
}


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
df_raw = loader.load_steo_dpr_data()
mapping_df = loader.load_dpr_mapping()

metadata_cols = ['id', 'name', 'release_date', 'uom']
date_columns = [col for col in df_raw.columns if col not in metadata_cols]

df_melted = pd.melt(df_raw, id_vars=metadata_cols, value_vars=date_columns,
                    var_name='delivery_month', value_name='value')
df_melted['delivery_month'] = pd.to_datetime(df_melted['delivery_month'])
df_melted = df_melted.merge(mapping_df[['id', 'region']], on='id', how='left')

release_dates = sorted(df_melted['release_date'].unique(), reverse=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _empty_fig(msg="No data available"):
    fig = go.Figure()
    fig.update_layout(
        annotations=[dict(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                          showarrow=False, font=dict(size=14, color=GRAY_500))],
        **{k: v for k, v in CHART_LAYOUT.items() if k not in ('xaxis', 'yaxis')},
    )
    return fig


def _base_layout(title, **overrides):
    layout = {**CHART_LAYOUT}
    layout["title"] = dict(text=title, font=dict(size=14))
    layout.update(overrides)
    return layout


def _hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _get_region_data(release_date, region):
    """Get pivoted time series for a single region and release date."""
    abbrev = REGION_ABBREV.get(region, '')
    if not abbrev:
        return pd.DataFrame()

    df_f = df_melted[
        (df_melted['release_date'] == release_date) &
        (df_melted['region'] == region)
    ].copy()

    if df_f.empty:
        return pd.DataFrame()

    pivot = df_f.pivot_table(index='delivery_month', columns='id',
                             values='value', aggfunc='first').reset_index()
    pivot = pivot.sort_values('delivery_month')

    result = pd.DataFrame({'month': pivot['delivery_month']})
    for metric, prefix in [('wells_drilled', 'NWD'), ('wells_completed', 'NWC'),
                           ('ducs', 'DUCS'), ('rigs', 'RIGS'),
                           ('new_well_oil', 'CONW'), ('new_well_oil_per_rig', 'CONWR'),
                           ('new_well_gas', 'NGNW'), ('new_well_gas_per_rig', 'NGNWR'),
                           ('wells_per_rig', 'NWR'),
                           ('existing_oil_decline', 'COEOP'), ('existing_gas_decline', 'NGEOP')]:
        col = f'{prefix}{abbrev}'
        result[metric] = pivot[col].values if col in pivot.columns else 0

    result = result.fillna(0)

    # Drop trailing rows where all key metrics are zero (empty forecast months)
    key_cols = ['wells_drilled', 'wells_completed', 'ducs']
    has_data = result[key_cols].any(axis=1)
    if has_data.any():
        last_valid = has_data[::-1].idxmax()
        result = result.loc[:last_valid].copy()

    result['duc_change'] = result['wells_drilled'] - result['wells_completed']
    result['completion_rate'] = np.where(
        result['wells_drilled'] > 0,
        result['wells_completed'] / result['wells_drilled'] * 100, 0)
    result['months_supply'] = np.where(
        result['wells_completed'] > 0,
        result['ducs'] / result['wells_completed'], 0)
    result['oil_per_well'] = np.where(
        result['wells_completed'] > 0,
        result['new_well_oil'] / result['wells_completed'], 0)
    result['gas_per_well'] = np.where(
        result['wells_completed'] > 0,
        result['new_well_gas'] / result['wells_completed'], 0)

    return result


def _get_all_regions_data(release_date):
    """Get aggregated data across all regions."""
    frames = {}
    for region in REGIONS:
        rd = _get_region_data(release_date, region)
        if not rd.empty:
            frames[region] = rd

    if not frames:
        return pd.DataFrame()

    # Use intersection of months across all regions
    common_months = None
    for f in frames.values():
        months_set = set(f['month'])
        common_months = months_set if common_months is None else common_months & months_set
    common_months = sorted(common_months)

    # Align all frames to common months
    aligned = {}
    for region, f in frames.items():
        aligned[region] = f[f['month'].isin(common_months)].sort_values('month').reset_index(drop=True)

    agg = pd.DataFrame({'month': common_months})
    sum_cols = ['wells_drilled', 'wells_completed', 'ducs', 'rigs',
                'new_well_oil', 'new_well_gas', 'existing_oil_decline', 'existing_gas_decline']
    for col in sum_cols:
        agg[col] = sum(f[col].values for f in aligned.values())

    agg['duc_change'] = agg['wells_drilled'] - agg['wells_completed']
    agg['completion_rate'] = np.where(
        agg['wells_drilled'] > 0,
        agg['wells_completed'] / agg['wells_drilled'] * 100, 0)
    agg['months_supply'] = np.where(
        agg['wells_completed'] > 0,
        agg['ducs'] / agg['wells_completed'], 0)
    agg['oil_per_well'] = np.where(
        agg['wells_completed'] > 0,
        agg['new_well_oil'] / agg['wells_completed'], 0)
    agg['gas_per_well'] = np.where(
        agg['wells_completed'] > 0,
        agg['new_well_gas'] / agg['wells_completed'], 0)
    agg['wells_per_rig'] = np.where(
        agg['rigs'] > 0,
        agg['wells_drilled'] / agg['rigs'], 0)

    return agg


def _get_data(release_date, region):
    """Dispatch to single region or all-region aggregation."""
    rd = pd.to_datetime(release_date)
    if region == 'All Regions':
        return _get_all_regions_data(rd)
    return _get_region_data(rd, region)


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
            html.Span(" m/m", style={
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


def _section_heading(text):
    return html.H4(text, style={
        "color": RED, "fontSize": "1.15em", "fontWeight": "700",
        "margin": "2rem 0 1rem 0",
        "borderBottom": f"2px solid {GRAY_200}", "paddingBottom": "6px",
    })


def _compute_stats_monthly(values):
    """Compute statistical metrics for monthly DPR series."""
    if values is None or len(values) < 3:
        return None
    s = pd.Series(values)
    current = s.iloc[-1]
    avg_3 = s.rolling(3, min_periods=1).mean().iloc[-1]
    avg_12 = s.rolling(12, min_periods=3).mean().iloc[-1] if len(s) >= 3 else current

    mean_12 = s.rolling(12, min_periods=3).mean().iloc[-1]
    std_12 = s.rolling(12, min_periods=3).std().iloc[-1]
    zscore = (current - mean_12) / std_12 if std_12 and std_12 > 0 else 0.0

    percentile = (s <= current).sum() / len(s) * 100

    mom = current - s.iloc[-2] if len(s) >= 2 else None
    mom_pct = (mom / s.iloc[-2] * 100) if mom is not None and s.iloc[-2] != 0 else None

    if len(s) >= 6:
        x = np.arange(min(12, len(s)), dtype=float)
        slope = float(np.polyfit(x, s.iloc[-len(x):].values, 1)[0])
    else:
        slope = None

    cv = (std_12 / mean_12 * 100) if mean_12 and mean_12 > 0 and std_12 else None

    return {
        'current': current,
        'avg_3': avg_3,
        'avg_12': avg_12,
        'zscore': zscore,
        'percentile': percentile,
        'mom': mom,
        'mom_pct': mom_pct,
        'slope': slope,
        'cv': cv,
    }


def _zscore_color(z):
    az = abs(z)
    if az > 2:
        return NEGATIVE
    if az > 1:
        return ORANGE
    return POSITIVE


def _fmt(val, fmt_str=".1f", suffix=""):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    return f"{val:{fmt_str}}{suffix}"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout = html.Div([

    # Header
    html.Div([
        html.Div([
            html.Div("DRILLING PRODUCTIVITY REPORT", style={
                "fontSize": "0.7rem", "fontWeight": "700", "letterSpacing": "0.15em",
                "color": GRAY_500, "marginBottom": "4px",
            }),
            html.H2("DUC Analysis", style={
                "color": GRAY_800, "fontWeight": "800", "margin": "0",
            }),
        ], style={"flex": "1"}),

        # Controls
        html.Div([
            html.Div([
                html.Label("Region", style={"fontSize": "0.75rem", "fontWeight": "600",
                                            "color": GRAY_500, "marginBottom": "2px"}),
                dcc.Dropdown(
                    id='p38-region',
                    options=[{'label': 'All Regions', 'value': 'All Regions'}] +
                            [{'label': r, 'value': r} for r in REGIONS],
                    value='Permian',
                    style={'width': '190px'},
                    clearable=False,
                ),
            ], style={'display': 'inline-block', 'marginRight': '16px'}),
            html.Div([
                html.Label("Release Date", style={"fontSize": "0.75rem", "fontWeight": "600",
                                                   "color": GRAY_500, "marginBottom": "2px"}),
                dcc.Dropdown(
                    id='p38-release',
                    options=[{'label': d.strftime('%Y-%m-%d'), 'value': d.isoformat()} for d in release_dates],
                    value=release_dates[0].isoformat() if release_dates else None,
                    style={'width': '160px'},
                    clearable=False,
                ),
            ], style={'display': 'inline-block', 'marginRight': '16px'}),
            html.Div([
                html.Label("Commodity", style={"fontSize": "0.75rem", "fontWeight": "600",
                                               "color": GRAY_500, "marginBottom": "2px"}),
                dcc.RadioItems(
                    id='p38-commodity',
                    options=[{'label': ' Oil', 'value': 'oil'}, {'label': ' Gas', 'value': 'gas'}],
                    value='oil',
                    inline=True,
                    style={"fontSize": "0.9rem", "marginTop": "6px"},
                    inputStyle={"marginRight": "4px"},
                    labelStyle={"marginRight": "14px"},
                ),
            ], style={'display': 'inline-block'}),
        ], style={"display": "flex", "alignItems": "flex-end"}),
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end",
              "marginBottom": "1.5rem", "flexWrap": "wrap", "gap": "1rem"}),

    # KPI Strip
    html.Div(id='p38-kpi-strip'),

    # Section 2: Inventory Dynamics
    _section_heading("Inventory Dynamics"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='p38-waterfall'), lg=6),
        dbc.Col(dcc.Graph(id='p38-duc-stacked'), lg=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='p38-duc-share'), lg=6),
        dbc.Col(dcc.Graph(id='p38-duc-heatmap'), lg=6),
    ], style={"marginTop": "8px"}),

    # Section 3: Drilling & Completion Efficiency
    _section_heading("Drilling & Completion Efficiency"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='p38-completion-rate'), lg=6),
        dbc.Col(dcc.Graph(id='p38-months-supply'), lg=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='p38-rigs-completions'), lg=6),
        dbc.Col(dcc.Graph(id='p38-wells-per-rig'), lg=6),
    ], style={"marginTop": "8px"}),

    # Section 4: Production Impact
    _section_heading("Production Impact"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='p38-prod-vs-completions'), lg=6),
        dbc.Col(dcc.Graph(id='p38-prod-per-well'), lg=6),
    ]),

    # Section 5: Statistical Analysis
    _section_heading("Statistical Analysis"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='p38-zscore'), lg=6),
        dbc.Col(html.Div(id='p38-stats-table'), lg=6),
    ]),

], style=PAGE_STYLE)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

# 1. KPI Strip
@callback(
    Output('p38-kpi-strip', 'children'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value'),
     Input('p38-commodity', 'value')]
)
def update_kpi_strip(region, release_date, commodity):
    if not release_date:
        return html.Div()
    data = _get_data(release_date, region)
    if data.empty or len(data) < 2:
        return html.Div("Insufficient data for KPIs", style={"color": GRAY_500})

    latest = data.iloc[-1]
    prior = data.iloc[-2]

    prod_key = 'oil_per_well' if commodity == 'oil' else 'gas_per_well'
    prod_label = 'OIL PER WELL' if commodity == 'oil' else 'GAS PER WELL'
    prod_unit = ' kbd' if commodity == 'oil' else ' mcfd'

    cards_config = [
        ('DUC INVENTORY', 'ducs', '', RED, ',.0f'),
        ('WELLS DRILLED', 'wells_drilled', '', BLUE, ',.0f'),
        ('WELLS COMPLETED', 'wells_completed', '', GREEN, ',.0f'),
        ('COMPLETION RATE', 'completion_rate', '%', ORANGE, '.1f'),
        ('DUC MONTHS OF SUPPLY', 'months_supply', ' mo', PURPLE, '.1f'),
        (prod_label, prod_key, prod_unit, GRAY_800, '.2f'),
    ]

    cols = []
    for title, key, suffix, color, fmt in cards_config:
        val = latest[key]
        prev = prior[key]
        chg = val - prev

        if key == 'completion_rate':
            val_str = f"{val:.1f}%"
            sign = "+" if chg >= 0 else ""
            chg_str = f"{sign}{chg:.1f} ppt"
        elif key in ('months_supply',):
            val_str = f"{val:.1f}{suffix}"
            sign = "+" if chg >= 0 else ""
            chg_str = f"{sign}{chg:.1f}"
        elif key in ('oil_per_well', 'gas_per_well'):
            val_str = f"{val:.2f}{suffix}"
            sign = "+" if chg >= 0 else ""
            chg_str = f"{sign}{chg:.2f}"
        else:
            val_str = f"{val:,.0f}"
            sign = "+" if chg >= 0 else ""
            chg_str = f"{sign}{chg:,.0f}"

        # For inventory metrics, negative change = drawdown = positive signal
        if key in ('ducs', 'months_supply'):
            is_positive = chg <= 0
        else:
            is_positive = chg >= 0

        cols.append(dbc.Col(
            _metric_card(title, val_str, chg_str, is_positive, color),
            lg=2, md=4, sm=6,
        ))

    return dbc.Row(cols, className="g-3")


# 2. Waterfall Chart
@callback(
    Output('p38-waterfall', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_waterfall(region, release_date):
    if not release_date:
        return _empty_fig()
    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    fig = go.Figure()
    months = data['month']

    # Wells drilled bars (positive)
    fig.add_trace(go.Bar(
        name='Wells Drilled', x=months, y=data['wells_drilled'],
        marker_color=BLUE, opacity=0.85,
        hovertemplate='Wells Drilled: %{y:,.0f}<extra></extra>',
    ))

    # Wells completed bars (negative for waterfall effect)
    fig.add_trace(go.Bar(
        name='Wells Completed', x=months, y=-data['wells_completed'],
        marker_color=GREEN, opacity=0.85,
        hovertemplate='Wells Completed: %{customdata:,.0f}<extra></extra>',
        customdata=data['wells_completed'],
    ))

    # DUC inventory line on right axis
    fig.add_trace(go.Scatter(
        name='DUC Inventory', x=months, y=data['ducs'],
        mode='lines+markers', yaxis='y2',
        line=dict(color=RED, width=3),
        marker=dict(size=5),
        hovertemplate='DUC Inventory: %{y:,.0f}<extra></extra>',
    ))

    label = REGION_SHORT.get(region, region)
    layout = _base_layout(f"{label} — DUC Inventory Flow")
    layout['barmode'] = 'relative'
    layout['yaxis']['title'] = 'Wells Drilled / Completed (Monthly)'
    layout['yaxis2'] = dict(title='DUC Inventory', overlaying='y', side='right', showgrid=False)
    layout['margin'] = dict(l=60, r=60, t=70, b=40)
    fig.update_layout(**layout)
    return fig


# 3. DUC Stacked Area (by region or single region with MA)
@callback(
    Output('p38-duc-stacked', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_duc_stacked(region, release_date):
    if not release_date:
        return _empty_fig()
    rd = pd.to_datetime(release_date)

    if region == 'All Regions':
        # Stacked area of all regions
        fig = go.Figure()
        region_vals = []
        for r in REGIONS:
            data = _get_region_data(rd, r)
            if not data.empty:
                last_val = data['ducs'].iloc[-1]
                region_vals.append((r, data, last_val))

        # Sort by latest value (largest on bottom)
        region_vals.sort(key=lambda x: x[2], reverse=True)

        for r, data, _ in region_vals:
            fig.add_trace(go.Scatter(
                x=data['month'], y=data['ducs'],
                name=REGION_SHORT[r], mode='lines',
                line=dict(width=0.5, color=REGION_COLORS[r]),
                stackgroup='one',
                fillcolor=_hex_to_rgba(REGION_COLORS[r], 0.6),
            ))

        layout = _base_layout("DUC Inventory by Region (Stacked)")
        layout['yaxis']['title'] = 'Well Count'
        fig.update_layout(**layout)
        return fig
    else:
        # Single region with 12mo MA
        data = _get_data(release_date, region)
        if data.empty:
            return _empty_fig()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data['month'], y=data['ducs'],
            name='DUC Inventory', mode='lines',
            line=dict(color=RED, width=2.5),
        ))
        if len(data) >= 6:
            ma = data['ducs'].rolling(6, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=data['month'], y=ma,
                name='6mo MA', mode='lines',
                line=dict(color=GRAY_300, width=2, dash='dash'),
            ))

        label = REGION_SHORT.get(region, region)
        layout = _base_layout(f"{label} — DUC Inventory Trend")
        layout['yaxis']['title'] = 'Well Count'
        fig.update_layout(**layout)
        return fig


# 4. DUC Share (100% stacked area)
@callback(
    Output('p38-duc-share', 'figure'),
    Input('p38-release', 'value')
)
def update_duc_share(release_date):
    if not release_date:
        return _empty_fig()
    rd = pd.to_datetime(release_date)

    fig = go.Figure()
    for r in REGIONS:
        data = _get_region_data(rd, r)
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['month'], y=data['ducs'],
                name=REGION_SHORT[r], mode='lines',
                line=dict(width=0.5, color=REGION_COLORS[r]),
                stackgroup='one', groupnorm='percent',
                fillcolor=_hex_to_rgba(REGION_COLORS[r], 0.6),
            ))

    layout = _base_layout("DUC Share by Region")
    layout['yaxis']['title'] = '% of Total'
    layout['yaxis']['range'] = [0, 100]
    fig.update_layout(**layout)
    return fig


# 5. Regional DUC Heatmap
@callback(
    Output('p38-duc-heatmap', 'figure'),
    Input('p38-release', 'value')
)
def update_duc_heatmap(release_date):
    if not release_date:
        return _empty_fig()
    rd = pd.to_datetime(release_date)

    # Collect last 6 months of DUC data for each region
    all_data = {}
    all_months = set()
    for r in REGIONS:
        data = _get_region_data(rd, r)
        if not data.empty:
            tail = data.tail(6)
            all_data[r] = tail
            all_months.update(tail['month'].tolist())

    if not all_data:
        return _empty_fig()

    months_sorted = sorted(all_months)[-6:]
    month_labels = [m.strftime('%Y-%m') for m in months_sorted]

    z_vals = []
    text_vals = []
    y_labels = []
    for r in REGIONS:
        if r in all_data:
            row_data = all_data[r].set_index('month')
            row_z = []
            row_t = []
            for m in months_sorted:
                val = row_data.loc[m, 'ducs'] if m in row_data.index else 0
                row_z.append(val)
                row_t.append(f"{val:,.0f}")
            z_vals.append(row_z)
            text_vals.append(row_t)
            y_labels.append(REGION_SHORT[r])

    fig = go.Figure(go.Heatmap(
        z=z_vals, x=month_labels, y=y_labels,
        text=text_vals, texttemplate="%{text}",
        textfont=dict(size=12, color="black"),
        colorscale=COLORSCALE_HEATMAP, reversescale=True,
        hovertemplate='%{y}<br>%{x}: %{text} wells<extra></extra>',
        showscale=True,
        colorbar=dict(title="Wells", len=0.8),
    ))

    layout = _base_layout("Regional DUC Heatmap (Last 6 Months)")
    layout['yaxis'] = dict(autorange='reversed')
    layout['xaxis'] = dict(side='top')
    layout['height'] = CHART_HEIGHT
    fig.update_layout(**layout)
    return fig


# 6. Completion Rate Trend
@callback(
    Output('p38-completion-rate', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_completion_rate(region, release_date):
    if not release_date:
        return _empty_fig()
    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    fig = go.Figure()

    # Net DUC change bars on right axis — color by direction
    colors = [BLUE if v >= 0 else GREEN for v in data['duc_change']]
    fig.add_trace(go.Bar(
        name='Net DUC Change', x=data['month'], y=data['duc_change'],
        marker_color=colors, opacity=0.5, yaxis='y2',
        hovertemplate='Net Change: %{y:+,.0f}<extra></extra>',
    ))

    # Completion rate line on left axis
    fig.add_trace(go.Scatter(
        name='Completion Rate', x=data['month'], y=data['completion_rate'],
        mode='lines', line=dict(color=RED, width=2.5),
        hovertemplate='Completion Rate: %{y:.1f}%<extra></extra>',
    ))

    # 3-month MA
    if len(data) >= 3:
        ma = data['completion_rate'].rolling(3, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            name='3mo MA', x=data['month'], y=ma,
            mode='lines', line=dict(color=GRAY_300, width=2, dash='dash'),
        ))

    # 100% reference line
    fig.add_hline(y=100, line_dash="dash", line_color=GRAY_500, opacity=0.5,
                  annotation_text="100% (Balanced)", annotation_position="top right")

    label = REGION_SHORT.get(region, region)
    layout = _base_layout(f"{label} — Completion Rate vs DUC Change")
    layout['yaxis']['title'] = 'Completion Rate (%)'
    layout['yaxis2'] = dict(title='Net DUC Change (wells)', overlaying='y',
                            side='right', showgrid=False)
    layout['margin'] = dict(l=60, r=60, t=70, b=40)
    fig.update_layout(**layout)
    return fig


# 7. DUC Months of Supply with zone shading
@callback(
    Output('p38-months-supply', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_months_supply(region, release_date):
    if not release_date:
        return _empty_fig()
    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    fig = go.Figure()

    # Zone shading
    fig.add_hrect(y0=0, y1=6, fillcolor="rgba(74,176,77,0.07)", line_width=0,
                  annotation_text="Tight", annotation_position="top left")
    fig.add_hrect(y0=6, y1=12, fillcolor="rgba(255,255,255,0)", line_width=0,
                  annotation_text="Normal", annotation_position="top left")
    fig.add_hrect(y0=12, y1=18, fillcolor="rgba(246,142,47,0.07)", line_width=0,
                  annotation_text="Elevated", annotation_position="top left")
    fig.add_hrect(y0=18, y1=36, fillcolor="rgba(236,0,43,0.07)", line_width=0,
                  annotation_text="Backlog", annotation_position="top left")

    fig.add_trace(go.Scatter(
        name='Months of Supply', x=data['month'], y=data['months_supply'],
        mode='lines', line=dict(color=BLACK, width=2.5),
        hovertemplate='%{y:.1f} months<extra></extra>',
    ))

    if len(data) >= 6:
        ma = data['months_supply'].rolling(6, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            name='6mo MA', x=data['month'], y=ma,
            mode='lines', line=dict(color=GRAY_300, width=2, dash='dash'),
        ))

    label = REGION_SHORT.get(region, region)
    layout = _base_layout(f"{label} — DUC Months of Supply")
    layout['yaxis']['title'] = 'Months'
    max_val = data['months_supply'].max()
    layout['yaxis']['range'] = [0, max(max_val * 1.15, 20)]
    fig.update_layout(**layout)
    return fig


# 8. Rig Count vs Completions
@callback(
    Output('p38-rigs-completions', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_rigs_completions(region, release_date):
    if not release_date:
        return _empty_fig()
    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name='Active Rigs', x=data['month'], y=data['rigs'],
        mode='lines', line=dict(color=BLUE, width=2.5),
        hovertemplate='Rigs: %{y:,.0f}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        name='Wells Completed', x=data['month'], y=data['wells_completed'],
        mode='lines', line=dict(color=GREEN, width=2.5),
        yaxis='y2',
        hovertemplate='Completed: %{y:,.0f}<extra></extra>',
    ))

    label = REGION_SHORT.get(region, region)
    layout = _base_layout(f"{label} — Rig Count vs Completions")
    layout['yaxis'] = dict(title='Active Rigs', titlefont=dict(color=BLUE),
                           tickfont=dict(color=BLUE), showgrid=True, gridcolor=GRAY_200)
    layout['yaxis2'] = dict(title='Wells Completed', titlefont=dict(color=GREEN),
                            tickfont=dict(color=GREEN), overlaying='y', side='right', showgrid=False)
    layout['margin'] = dict(l=60, r=60, t=70, b=40)
    fig.update_layout(**layout)
    return fig


# 9. Wells Per Rig Efficiency
@callback(
    Output('p38-wells-per-rig', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_wells_per_rig(region, release_date):
    if not release_date:
        return _empty_fig()

    if region == 'All Regions':
        # Show one line per region
        rd = pd.to_datetime(release_date)
        fig = go.Figure()
        for r in REGIONS:
            data = _get_region_data(rd, r)
            if not data.empty and data['wells_per_rig'].sum() > 0:
                fig.add_trace(go.Scatter(
                    name=REGION_SHORT[r], x=data['month'], y=data['wells_per_rig'],
                    mode='lines', line=dict(color=REGION_COLORS[r], width=2),
                ))
        layout = _base_layout("Wells Drilled per Rig by Region")
        layout['yaxis']['title'] = 'Wells / Rig'
        fig.update_layout(**layout)
        return fig

    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name='Wells / Rig', x=data['month'], y=data['wells_per_rig'],
        mode='lines', line=dict(color=PURPLE, width=2.5),
        hovertemplate='%{y:.2f} wells/rig<extra></extra>',
    ))

    if len(data) >= 6:
        ma = data['wells_per_rig'].rolling(6, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            name='6mo MA', x=data['month'], y=ma,
            mode='lines', line=dict(color=GRAY_300, width=2, dash='dash'),
        ))

    label = REGION_SHORT.get(region, region)
    layout = _base_layout(f"{label} — Wells Drilled per Rig")
    layout['yaxis']['title'] = 'Wells / Rig'
    fig.update_layout(**layout)
    return fig


# 10. Production vs Completions
@callback(
    Output('p38-prod-vs-completions', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value'),
     Input('p38-commodity', 'value')]
)
def update_prod_vs_completions(region, release_date, commodity):
    if not release_date:
        return _empty_fig()
    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    prod_col = 'new_well_oil' if commodity == 'oil' else 'new_well_gas'
    prod_label = 'New Well Oil (kbd)' if commodity == 'oil' else 'New Well Gas (mcfd)'
    unit = 'kbd' if commodity == 'oil' else 'mcfd'

    fig = go.Figure()

    # Production as filled area
    fig.add_trace(go.Scatter(
        name=prod_label, x=data['month'], y=data[prod_col],
        mode='lines', fill='tozeroy',
        line=dict(color=GREEN, width=1),
        fillcolor=_hex_to_rgba(GREEN, 0.25),
        hovertemplate=f'Production: %{{y:,.1f}} {unit}<extra></extra>',
    ))

    # Completions as line on right axis
    fig.add_trace(go.Scatter(
        name='Wells Completed', x=data['month'], y=data['wells_completed'],
        mode='lines', yaxis='y2',
        line=dict(color=RED, width=2.5),
        hovertemplate='Completed: %{y:,.0f}<extra></extra>',
    ))

    label = REGION_SHORT.get(region, region)
    commodity_label = 'Oil' if commodity == 'oil' else 'Gas'
    layout = _base_layout(f"{label} — New Well {commodity_label} vs Completions")
    layout['yaxis'] = dict(title=f'Production ({unit})', showgrid=True, gridcolor=GRAY_200)
    layout['yaxis2'] = dict(title='Wells Completed', overlaying='y', side='right', showgrid=False)
    layout['margin'] = dict(l=60, r=60, t=70, b=40)
    fig.update_layout(**layout)
    return fig


# 11. Production per Completed Well
@callback(
    Output('p38-prod-per-well', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value'),
     Input('p38-commodity', 'value')]
)
def update_prod_per_well(region, release_date, commodity):
    if not release_date:
        return _empty_fig()

    prod_key = 'oil_per_well' if commodity == 'oil' else 'gas_per_well'
    unit = 'kbd/well' if commodity == 'oil' else 'mcfd/well'
    commodity_label = 'Oil' if commodity == 'oil' else 'Gas'

    if region == 'All Regions':
        rd = pd.to_datetime(release_date)
        fig = go.Figure()
        for r in REGIONS:
            data = _get_region_data(rd, r)
            if not data.empty and data[prod_key].sum() > 0:
                fig.add_trace(go.Scatter(
                    name=REGION_SHORT[r], x=data['month'], y=data[prod_key],
                    mode='lines', line=dict(color=REGION_COLORS[r], width=2),
                ))
        layout = _base_layout(f"{commodity_label} per Completed Well — All Regions")
        layout['yaxis']['title'] = unit
        fig.update_layout(**layout)
        return fig

    data = _get_data(release_date, region)
    if data.empty:
        return _empty_fig()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name=f'{commodity_label} / Well', x=data['month'], y=data[prod_key],
        mode='lines', line=dict(color=ORANGE, width=2.5),
        hovertemplate=f'%{{y:.2f}} {unit}<extra></extra>',
    ))

    if len(data) >= 6:
        ma = data[prod_key].rolling(6, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            name='6mo MA', x=data['month'], y=ma,
            mode='lines', line=dict(color=GRAY_300, width=2, dash='dash'),
        ))

    label = REGION_SHORT.get(region, region)
    layout = _base_layout(f"{label} — {commodity_label} per Completed Well")
    layout['yaxis']['title'] = unit
    fig.update_layout(**layout)
    return fig


# 12. Z-Score Anomaly Detection
@callback(
    Output('p38-zscore', 'figure'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value')]
)
def update_zscore(region, release_date):
    if not release_date:
        return _empty_fig()
    data = _get_data(release_date, region)
    if data.empty or len(data) < 6:
        return _empty_fig("Not enough data for z-score analysis")

    s = pd.Series(data['ducs'].values, index=data['month'])
    rolling_mean = s.rolling(12, min_periods=3).mean()
    rolling_std = s.rolling(12, min_periods=3).std()
    zscore = (s - rolling_mean) / rolling_std
    upper_band = rolling_mean + 2 * rolling_std
    lower_band = rolling_mean - 2 * rolling_std

    label = REGION_SHORT.get(region, region)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.6, 0.4], vertical_spacing=0.08,
        subplot_titles=[
            f"{label} — DUC Inventory with Confidence Band",
            "Z-Score (12-Month Rolling)"
        ],
    )

    # Top: confidence band
    fig.add_trace(go.Scatter(
        x=s.index, y=upper_band, mode='lines', name='Upper (+2σ)',
        line=dict(width=0), showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=s.index, y=lower_band, mode='lines', name='±2σ Band',
        line=dict(width=0), fill='tonexty',
        fillcolor='rgba(0,173,239,0.12)',
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=s.index, y=s.values, mode='lines', name='DUC Inventory',
        line=dict(color=RED, width=2.5),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=s.index, y=rolling_mean, mode='lines', name='12mo Mean',
        line=dict(color=GRAY_300, width=1.5, dash='dash'),
    ), row=1, col=1)

    # Bottom: z-score with colored zones
    fig.add_hrect(y0=-1, y1=1, fillcolor="rgba(74,176,77,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=1, y1=2, fillcolor="rgba(246,142,47,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=-2, y1=-1, fillcolor="rgba(246,142,47,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=2, y1=4, fillcolor="rgba(236,0,43,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=-4, y1=-2, fillcolor="rgba(236,0,43,0.08)", line_width=0, row=2, col=1)

    fig.add_trace(go.Scatter(
        x=s.index, y=zscore, mode='lines', name='Z-Score',
        line=dict(color=BLUE, width=2),
    ), row=2, col=1)

    # Anomaly markers
    anomaly_mask = (zscore.abs() > 2).fillna(False)
    if anomaly_mask.any():
        fig.add_trace(go.Scatter(
            x=zscore[anomaly_mask].index.tolist(),
            y=zscore[anomaly_mask].values.tolist(),
            mode='markers', name='Anomaly (|z|>2)',
            marker=dict(color=RED, size=8, symbol='diamond'),
        ), row=2, col=1)

    fig.add_hline(y=0, line_dash="solid", line_color=GRAY_500, opacity=0.4, row=2, col=1)

    fig.update_layout(
        height=480, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=60, r=20, t=50, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode='x unified', font=dict(family="Montserrat"),
    )
    fig.update_yaxes(title_text="Well Count", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)

    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=13, color=RED)

    return fig


# 13. Statistics Summary Table
@callback(
    Output('p38-stats-table', 'children'),
    [Input('p38-region', 'value'),
     Input('p38-release', 'value'),
     Input('p38-commodity', 'value')]
)
def update_stats_table(region, release_date, commodity):
    if not release_date:
        return html.Div("No data available")
    data = _get_data(release_date, region)
    if data.empty or len(data) < 3:
        return html.Div("Insufficient data for statistics", style={"color": GRAY_500})

    prod_key = 'oil_per_well' if commodity == 'oil' else 'gas_per_well'
    prod_label = 'Oil/Well' if commodity == 'oil' else 'Gas/Well'

    columns = {}
    count_cols = set()

    for key, label in [('ducs', 'DUC Count'), ('wells_drilled', 'Drilled'),
                       ('wells_completed', 'Completed')]:
        columns[label] = _compute_stats_monthly(data[key].values)
        count_cols.add(label)

    columns['Comp Rate %'] = _compute_stats_monthly(data['completion_rate'].values)
    columns['Mo Supply'] = _compute_stats_monthly(data['months_supply'].values)

    if not columns:
        return html.Div("No data available for statistics")

    col_names = list(columns.keys())

    metric_rows = [
        ('Current', 'current', lambda v, cn: _fmt(v, ",.0f") if cn in count_cols else _fmt(v, ".1f")),
        ('3mo Avg', 'avg_3', lambda v, cn: _fmt(v, ",.0f") if cn in count_cols else _fmt(v, ".1f")),
        ('12mo Avg', 'avg_12', lambda v, cn: _fmt(v, ",.0f") if cn in count_cols else _fmt(v, ".1f")),
        ('Z-Score', 'zscore', lambda v, cn: _fmt(v, "+.2f")),
        ('Percentile', 'percentile', lambda v, cn: _fmt(v, ".0f", "th")),
        ('MoM Chg', 'mom', lambda v, cn: _fmt(v, "+,.0f") if cn in count_cols else _fmt(v, "+.1f")),
        ('MoM %', 'mom_pct', lambda v, cn: _fmt(v, "+.1f", "%")),
        ('Trend', 'slope', lambda v, cn: _fmt(v, "+,.1f", "/mo") if cn in count_cols else _fmt(v, "+.2f", "/mo")),
        ('Volatility', 'cv', lambda v, cn: _fmt(v, ".1f", "%")),
    ]

    header = html.Tr(
        [html.Th("Metric", style={"padding": "8px 10px", "textAlign": "left",
                                   "borderBottom": f"2px solid {RED}",
                                   "color": RED, "fontWeight": "700", "fontSize": "0.82em"})] +
        [html.Th(cn, style={"padding": "8px 10px", "textAlign": "right",
                            "borderBottom": f"2px solid {RED}",
                            "color": RED, "fontWeight": "700", "fontSize": "0.82em"})
         for cn in col_names]
    )

    rows = []
    for i, (label, key, formatter) in enumerate(metric_rows):
        bg = "white" if i % 2 == 0 else GRAY_50
        cells = [html.Td(label, style={
            "padding": "6px 10px", "fontWeight": "600", "fontSize": "0.82em", "color": GRAY_500,
        })]
        for cn in col_names:
            stats = columns.get(cn)
            val = stats[key] if stats else None
            cell_style = {
                "padding": "6px 10px", "textAlign": "right",
                "fontWeight": "700", "fontSize": "0.85em",
            }
            if key == 'zscore' and val is not None:
                cell_style["color"] = "white"
                cell_style["backgroundColor"] = _zscore_color(val)
                cell_style["borderRadius"] = "4px"
            elif key in ('mom', 'mom_pct', 'slope') and val is not None:
                cell_style["color"] = POSITIVE if val >= 0 else NEGATIVE
            else:
                cell_style["color"] = BLACK
            cells.append(html.Td(formatter(val, cn), style=cell_style))
        rows.append(html.Tr(cells, style={"backgroundColor": bg}))

    label = REGION_SHORT.get(region, region)
    title = html.Div(
        f"Statistics Summary — {label}",
        style={"fontSize": "14px", "fontWeight": "700", "color": RED, "marginBottom": "10px"},
    )

    table = html.Table(
        [header] + rows,
        style={
            "width": "100%", "borderCollapse": "collapse",
            "backgroundColor": "white", "borderRadius": "8px",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
        },
    )

    return html.Div([title, table], style={"padding": "10px"})
