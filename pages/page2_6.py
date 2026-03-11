from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from src.wps.ag_calculations import DataProcessor
from src.utils.variables import default_start_date_eia_wps_table, default_end_date_eia_wps_table
from src.utils.colors import (
    RED, BLUE, ORANGE, GREEN, PURPLE, POSITIVE, NEGATIVE,
    GRAY_50, GRAY_200, GRAY_300, GRAY_500, BLACK
)

# Initialize the data processor
processor = DataProcessor()

default_start_date = default_start_date_eia_wps_table
default_end_date = default_end_date_eia_wps_table

try:
    df, columnDefinitions = processor.get_data(default_start_date, default_end_date)
except Exception as e:
    print(f"Error loading initial data for page2_6: {e}")
    df = pd.DataFrame()
    columnDefinitions = []

# ── PADD Series ID Map ────────────────────────────────────────────────
PADD_SERIES = {
    'US': {
        'crude_runs': 'WCRRIUS2',
        'gross_runs': 'WGIRIUS2',
        'feedstock_runs': 'feedstockRunsUS',
        'capacity': 'WOCLEUS2',
        'utilization': 'WPULEUS3',
        'crude_imports': 'WCEIMUS2',
    },
    'P1': {
        'crude_runs': 'WCRRIP12',
        'gross_runs': 'WGIRIP12',
        'feedstock_runs': 'feddStockRunsP1',
        'capacity': 'W_NA_YRL_R10_MBBLD',
        'utilization': 'W_NA_YUP_R10_PER',
        'crude_imports': 'WCEIMP12',
    },
    'P2': {
        'crude_runs': 'WCRRIP22',
        'gross_runs': 'WGIRIP22',
        'feedstock_runs': 'feedstockRunsP2',
        'capacity': 'W_NA_YRL_R20_MBBLD',
        'utilization': 'W_NA_YUP_R20_PER',
        'crude_imports': 'WCEIMP22',
    },
    'P3': {
        'crude_runs': 'WCRRIP32',
        'gross_runs': 'WGIRIP32',
        'feedstock_runs': 'feedstockRunsP3',
        'capacity': 'W_NA_YRL_R30_MBBLD',
        'utilization': 'W_NA_YUP_R30_PER',
        'crude_imports': 'WCEIMP32',
    },
    'P4': {
        'crude_runs': 'WCRRIP42',
        'gross_runs': 'WGIRIP42',
        'feedstock_runs': 'feedstockRunsP4',
        'capacity': 'W_NA_YRL_R40_MBBLD',
        'utilization': 'W_NA_YUP_R40_PER',
        'crude_imports': 'WCEIMP42',
    },
    'P5': {
        'crude_runs': 'WCRRIP52',
        'gross_runs': 'WGIRIP52',
        'feedstock_runs': 'feedstockRunsP5',
        'capacity': 'W_NA_YRL_R50_MBBLD',
        'utilization': 'W_NA_YUP_R50_PER',
        'crude_imports': 'WCEIMP52',
    },
}

PADD_LABELS = {
    'US': 'United States',
    'P1': 'PADD 1 — East Coast',
    'P2': 'PADD 2 — Midwest',
    'P3': 'PADD 3 — Gulf Coast',
    'P4': 'PADD 4 — Rocky Mountain',
    'P5': 'PADD 5 — West Coast',
}

# ── Helpers ───────────────────────────────────────────────────────────

def extract_time_series(data_row):
    if data_row is None or (isinstance(data_row, pd.Series) and data_row.empty):
        return [], []
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in data_row.index if col not in metadata_cols]
    pairs = []
    for col in date_cols:
        try:
            date = pd.to_datetime(col, format='%m/%d/%y')
            value = data_row[col]
            if pd.notna(value):
                pairs.append((date, float(value)))
        except Exception:
            continue
    pairs.sort(key=lambda x: x[0])
    dates = [p[0] for p in pairs]
    values = [p[1] for p in pairs]
    return dates, values


def get_series_row(df, series_id):
    row = df[df['id'] == series_id]
    if row.empty:
        return None
    return row.iloc[0]


def compute_ratio_series(dates_num, vals_num, dates_den, vals_den):
    num_map = dict(zip(dates_num, vals_num))
    den_map = dict(zip(dates_den, vals_den))
    common = sorted(set(dates_num) & set(dates_den))
    out_dates, out_vals = [], []
    for d in common:
        if den_map[d] != 0:
            out_dates.append(d)
            out_vals.append(num_map[d] / den_map[d] * 100)
    return out_dates, out_vals


def _empty_fig(msg="No data available"):
    return go.Figure().update_layout(
        title=msg, plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )


def _base_layout(title, yaxis_title="", height=340):
    return dict(
        title=dict(text=title, font=dict(size=15, color=RED)),
        xaxis_title="",
        yaxis_title=yaxis_title,
        hovermode='x unified',
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=20, t=70, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

# ── KPI card builder ──────────────────────────────────────────────────

def _kpi_card(label, value_str, delta_str=None, delta_color=None):
    children = [
        html.Div(label, style={
            "fontSize": "0.8em", "color": GRAY_500, "fontWeight": "600",
            "textTransform": "uppercase", "letterSpacing": "0.5px", "marginBottom": "4px",
        }),
        html.Div(value_str, style={
            "fontSize": "1.8em", "fontWeight": "700", "color": BLACK, "lineHeight": "1.1",
        }),
    ]
    if delta_str is not None:
        children.append(html.Div(delta_str, style={
            "fontSize": "0.85em", "fontWeight": "600",
            "color": delta_color or GRAY_500, "marginTop": "2px",
        }))
    return html.Div(children, style={
        "flex": "1", "textAlign": "center", "padding": "12px 8px",
        "backgroundColor": "white", "borderRadius": "8px",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
        "border": f"1px solid {GRAY_200}", "minWidth": "130px",
    })


# ── Layout ────────────────────────────────────────────────────────────

layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("Runs Analysis", style={"fontSize": "2.5em", "color": BLUE, "margin": "0", "fontWeight": "700"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center"}),

        html.Div([
            html.Label("Region:", style={"marginRight": "8px", "fontWeight": "600", "color": GRAY_500}),
            dcc.Dropdown(
                id='padd-selector-p13',
                options=[{'label': v, 'value': k} for k, v in PADD_LABELS.items()],
                value='US',
                clearable=False,
                style={"width": "260px"},
            ),
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range-p13',
                min_date_allowed='2010-01-01',
                max_date_allowed='2030-12-31',
                initial_visible_month=default_start_date,
                start_date=default_start_date,
                end_date=default_end_date,
                display_format='YYYY-MM-DD',
                className="custom-date-picker",
            ),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"}),
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),

    # Main scrollable content
    html.Div([
        # KPI strip
        html.Div(id='kpi-strip-p13', style={
            "display": "flex", "gap": "12px", "marginBottom": "20px", "flexWrap": "wrap",
        }),

        # ── Throughput ──
        html.H2("Throughput", style={"color": RED, "fontSize": "1.3em", "margin": "0 0 8px 0", "borderBottom": f"2px solid {GRAY_200}", "paddingBottom": "4px"}),
        html.Div([
            html.Div([
                dcc.Graph(id="runs-vs-capacity-p13", style={"height": "340px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            html.Div([
                dcc.Graph(id="imports-pct-runs-p13", style={"height": "340px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "16px"}),

        # ── Utilization ──
        html.H2("Utilization", style={"color": RED, "fontSize": "1.3em", "margin": "0 0 8px 0", "borderBottom": f"2px solid {GRAY_200}", "paddingBottom": "4px"}),
        html.Div([
            html.Div([
                dcc.Graph(id="utilization-trend-p13", style={"height": "340px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            html.Div([
                dcc.Graph(id="utilization-seasonality-p13", style={"height": "340px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "16px"}),

        # ── Feedstock ──
        html.H2("Feedstock", style={"color": RED, "fontSize": "1.3em", "margin": "0 0 8px 0", "borderBottom": f"2px solid {GRAY_200}", "paddingBottom": "4px"}),
        html.Div([
            html.Div([
                dcc.Graph(id="feedstock-solo-p13", style={"height": "340px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            html.Div([
                dcc.Graph(id="gross-attribution-p13", style={"height": "340px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "16px"}),

        # ── Statistics ──
        html.H2("Statistics", style={"color": RED, "fontSize": "1.3em", "margin": "0 0 8px 0", "borderBottom": f"2px solid {GRAY_200}", "paddingBottom": "4px"}),
        html.Div([
            html.Div([
                dcc.Graph(id="zscore-chart-p13", style={"height": "420px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            html.Div([
                html.Div(id="stats-summary-p13", style={"height": "420px", "overflow": "auto"})
            ], style={"width": "49%"}),
        ], style={"display": "flex"}),
    ], style={"padding": "20px", "height": "88vh", "overflow": "auto", "backgroundColor": GRAY_50}),

    # Hidden store
    dcc.Store(id='current-data-store-p13', data=df.to_dict('records') if not df.empty else []),

], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# ── Callbacks ─────────────────────────────────────────────────────────

# 1. Data store
@callback(
    Output("current-data-store-p13", "data"),
    [Input("date-picker-range-p13", "start_date"),
     Input("date-picker-range-p13", "end_date")]
)
def update_data_store(start_date, end_date):
    try:
        df, _ = processor.get_data(start_date, end_date)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error updating data store: {e}")
        return []


# 2. KPI strip
@callback(
    Output("kpi-strip-p13", "children"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_kpi_strip(data, padd):
    if not data:
        return html.Div("No data available")
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])
    cards = []

    metrics = [
        ('crude_runs', 'Crude Runs', 'kbd'),
        ('gross_runs', 'Gross Runs', 'kbd'),
        ('feedstock_runs', 'Feedstock Runs', 'kbd'),
        ('capacity', 'CDU Capacity', 'kbd'),
        ('utilization', 'Utilization', '%'),
    ]

    for key, label, unit in metrics:
        row = get_series_row(df, series[key])
        if row is not None:
            dates, values = extract_time_series(row)
            if values:
                current = values[-1]
                if unit == '%':
                    val_str = f"{current:.1f}%"
                else:
                    val_str = f"{current:,.0f}"
                if len(values) >= 2:
                    delta = current - values[-2]
                    if unit == '%':
                        delta_str = f"{delta:+.1f} ppt WoW"
                    else:
                        delta_str = f"{delta:+,.0f} WoW"
                    delta_color = POSITIVE if delta >= 0 else NEGATIVE
                else:
                    delta_str = None
                    delta_color = None
                cards.append(_kpi_card(label, val_str, delta_str, delta_color))
            else:
                cards.append(_kpi_card(label, "—"))
        else:
            cards.append(_kpi_card(label, "—"))

    # Imports as % of runs (computed)
    imp_row = get_series_row(df, series['crude_imports'])
    run_row = get_series_row(df, series['crude_runs'])
    if imp_row is not None and run_row is not None:
        imp_d, imp_v = extract_time_series(imp_row)
        run_d, run_v = extract_time_series(run_row)
        ratio_d, ratio_v = compute_ratio_series(imp_d, imp_v, run_d, run_v)
        if ratio_v:
            current = ratio_v[-1]
            val_str = f"{current:.1f}%"
            if len(ratio_v) >= 2:
                delta = current - ratio_v[-2]
                delta_str = f"{delta:+.1f} ppt WoW"
                delta_color = POSITIVE if delta <= 0 else NEGATIVE  # lower import dependency is positive
            else:
                delta_str = None
                delta_color = None
            cards.append(_kpi_card("Imports % of Runs", val_str, delta_str, delta_color))
        else:
            cards.append(_kpi_card("Imports % of Runs", "—"))
    else:
        cards.append(_kpi_card("Imports % of Runs", "—"))

    return cards


# 3. Crude Runs vs Gross Runs vs Capacity
@callback(
    Output("runs-vs-capacity-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_runs_vs_capacity(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])
    fig = go.Figure()

    traces = [
        ('crude_runs', 'Crude Runs', RED, 'solid'),
        ('gross_runs', 'Gross Runs', BLUE, 'solid'),
        ('capacity', 'CDU Capacity', ORANGE, 'dash'),
    ]

    for key, name, color, dash in traces:
        row = get_series_row(df, series[key])
        if row is not None:
            dates, values = extract_time_series(row)
            if dates:
                fig.add_trace(go.Scatter(
                    x=dates, y=values, mode='lines', name=name,
                    line=dict(color=color, width=2.5, dash=dash),
                ))

    # Add fill between capacity and crude runs to show spare capacity
    cap_row = get_series_row(df, series['capacity'])
    run_row = get_series_row(df, series['crude_runs'])
    if cap_row is not None and run_row is not None:
        cap_d, cap_v = extract_time_series(cap_row)
        run_d, run_v = extract_time_series(run_row)
        cap_map = dict(zip(cap_d, cap_v))
        run_map = dict(zip(run_d, run_v))
        common = sorted(set(cap_d) & set(run_d))
        if common:
            spare_dates = common
            spare_vals = [cap_map[d] - run_map[d] for d in common]
            fig.add_trace(go.Scatter(
                x=spare_dates, y=spare_vals, mode='lines', name='Spare Capacity',
                line=dict(color=GREEN, width=1.5, dash='dot'),
                yaxis='y2',
            ))

    layout_opts = _base_layout(
        f"Crude Runs vs Gross Runs vs Capacity — {PADD_LABELS.get(padd, padd)}",
        yaxis_title="kbd",
    )
    layout_opts['yaxis2'] = dict(
        title='Spare Capacity (kbd)', overlaying='y', side='right',
        showgrid=False,
    )
    fig.update_layout(**layout_opts)
    return fig


# 4. Imports as % of Refinery Runs
@callback(
    Output("imports-pct-runs-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_imports_pct(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    imp_row = get_series_row(df, series['crude_imports'])
    run_row = get_series_row(df, series['crude_runs'])
    if imp_row is None or run_row is None:
        return _empty_fig("Import or runs data not available")

    imp_d, imp_v = extract_time_series(imp_row)
    run_d, run_v = extract_time_series(run_row)
    ratio_d, ratio_v = compute_ratio_series(imp_d, imp_v, run_d, run_v)

    if not ratio_v:
        return _empty_fig("Could not compute import ratio")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ratio_d, y=ratio_v, mode='lines', name='Imports % of Runs',
        line=dict(color=PURPLE, width=2),
        fill='tozeroy', fillcolor='rgba(106,27,154,0.15)',
    ))

    # 52-week moving average as reference
    if len(ratio_v) >= 52:
        ma_vals = pd.Series(ratio_v).rolling(52).mean().tolist()
        fig.add_trace(go.Scatter(
            x=ratio_d, y=ma_vals, mode='lines', name='52-Week Avg',
            line=dict(color=GRAY_300, width=2, dash='dash'),
        ))

    fig.update_layout(**_base_layout(
        f"Crude Imports as % of Refinery Runs — {PADD_LABELS.get(padd, padd)}",
        yaxis_title="%",
    ))
    return fig


# 5. Utilization Rate Trend
@callback(
    Output("utilization-trend-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_utilization_trend(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    row = get_series_row(df, series['utilization'])
    if row is None:
        return _empty_fig("Utilization data not available")

    dates, values = extract_time_series(row)
    if not dates:
        return _empty_fig("No utilization data")

    fig = go.Figure()

    # Color bands
    fig.add_hrect(y0=0, y1=75, fillcolor="rgba(236,0,43,0.07)", line_width=0, annotation_text="Low", annotation_position="top left")
    fig.add_hrect(y0=75, y1=85, fillcolor="rgba(246,142,47,0.07)", line_width=0)
    fig.add_hrect(y0=85, y1=95, fillcolor="rgba(74,176,77,0.07)", line_width=0, annotation_text="Target Zone", annotation_position="top left")
    fig.add_hrect(y0=95, y1=100, fillcolor="rgba(0,173,239,0.07)", line_width=0)

    fig.add_trace(go.Scatter(
        x=dates, y=values, mode='lines', name='Utilization',
        line=dict(color=RED, width=2.5),
    ))

    fig.add_hline(y=90, line_dash="dash", line_color=GRAY_500, opacity=0.6,
                  annotation_text="90% Reference", annotation_position="top right")

    layout_opts = _base_layout(
        f"Refinery Utilization Rate — {PADD_LABELS.get(padd, padd)}",
        yaxis_title="%",
    )
    layout_opts['yaxis'] = dict(range=[60, 100], title="%")
    fig.update_layout(**layout_opts)
    return fig


# 6. Utilization Seasonality
@callback(
    Output("utilization-seasonality-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_utilization_seasonality(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    row = get_series_row(df, series['utilization'])
    if row is None:
        return _empty_fig("Utilization data not available")

    dates, values = extract_time_series(row)
    if not dates:
        return _empty_fig("No utilization data")

    ts = pd.DataFrame({'date': dates, 'value': values})
    ts['year'] = ts['date'].dt.year
    ts['week'] = ts['date'].dt.isocalendar().week.astype(int)

    current_year = ts['year'].max()
    years_to_show = sorted([y for y in ts['year'].unique() if y >= current_year - 3], reverse=True)
    colors = [BLACK, BLUE, RED, GREEN, ORANGE]

    fig = go.Figure()

    for i, year in enumerate(years_to_show):
        yr_data = ts[ts['year'] == year].sort_values('week')
        fig.add_trace(go.Scatter(
            x=yr_data['week'], y=yr_data['value'],
            mode='lines', name=str(year),
            line=dict(color=colors[i % len(colors)], width=2.5 if i == 0 else 1.8),
        ))

    # 5-year average
    avg_years = [y for y in ts['year'].unique() if current_year - 5 <= y < current_year]
    if avg_years:
        avg_data = ts[ts['year'].isin(avg_years)].groupby('week')['value'].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=avg_data['week'], y=avg_data['value'],
            mode='lines', name='5yr Avg',
            line=dict(color=GRAY_300, width=3, dash='dash'),
        ))

    layout_opts = _base_layout(
        f"Utilization Seasonality — {PADD_LABELS.get(padd, padd)}",
        yaxis_title="%",
    )
    layout_opts['xaxis_title'] = "Week of Year"
    layout_opts['yaxis'] = dict(range=[60, 100], title="%")
    fig.update_layout(**layout_opts)
    return fig


# 7. Feedstock Runs (solo with 4-week MA)
@callback(
    Output("feedstock-solo-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_feedstock_solo(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    feed_row = get_series_row(df, series['feedstock_runs'])
    if feed_row is None:
        return _empty_fig("Feedstock data not available")

    dates, values = extract_time_series(feed_row)
    if not dates:
        return _empty_fig("No feedstock data")

    fig = go.Figure()

    # Weekly raw
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode='lines', name='Weekly',
        line=dict(color=ORANGE, width=1.5),
        opacity=0.6,
    ))

    # 4-week moving average
    if len(values) >= 4:
        ma4 = pd.Series(values).rolling(4).mean().tolist()
        fig.add_trace(go.Scatter(
            x=dates, y=ma4, mode='lines', name='4-Week Avg',
            line=dict(color=RED, width=2.5),
        ))

    fig.update_layout(**_base_layout(
        f"Feedstock Runs — {PADD_LABELS.get(padd, padd)}",
        yaxis_title="kbd",
    ))
    return fig


# 8. Gross Runs Attribution — dual axis (crude % left, feedstock % right)
@callback(
    Output("gross-attribution-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_gross_attribution(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    crude_row = get_series_row(df, series['crude_runs'])
    feed_row = get_series_row(df, series['feedstock_runs'])
    gross_row = get_series_row(df, series['gross_runs'])

    if crude_row is None or feed_row is None or gross_row is None:
        return _empty_fig("Runs data not available")

    c_d, c_v = extract_time_series(crude_row)
    f_d, f_v = extract_time_series(feed_row)
    g_d, g_v = extract_time_series(gross_row)

    c_map = dict(zip(c_d, c_v))
    f_map = dict(zip(f_d, f_v))
    g_map = dict(zip(g_d, g_v))
    common = sorted(set(c_d) & set(f_d) & set(g_d))

    if not common:
        return _empty_fig("Could not align runs data")

    crude_pct = []
    feed_pct = []
    for d in common:
        gross = g_map[d]
        if gross > 0:
            crude_pct.append(c_map[d] / gross * 100)
            feed_pct.append(f_map[d] / gross * 100)
        else:
            crude_pct.append(None)
            feed_pct.append(None)

    fig = go.Figure()

    # Crude % of gross — left axis (weekly + 4wk avg)
    fig.add_trace(go.Scatter(
        x=common, y=crude_pct, mode='lines', name='Crude / Gross (weekly)',
        line=dict(color=RED, width=1), opacity=0.4,
    ))
    if len(common) >= 4:
        crude_ma = pd.Series(crude_pct).rolling(4, min_periods=1).mean().tolist()
        fig.add_trace(go.Scatter(
            x=common, y=crude_ma, mode='lines', name='Crude / Gross (4wk avg)',
            line=dict(color=RED, width=2.5),
        ))

    # Feedstock % of gross — right axis (weekly + 4wk avg)
    fig.add_trace(go.Scatter(
        x=common, y=feed_pct, mode='lines', name='Feedstock / Gross (weekly)',
        line=dict(color=ORANGE, width=1), opacity=0.4,
        yaxis='y2',
    ))
    if len(common) >= 4:
        feed_ma = pd.Series(feed_pct).rolling(4, min_periods=1).mean().tolist()
        fig.add_trace(go.Scatter(
            x=common, y=feed_ma, mode='lines', name='Feedstock / Gross (4wk avg)',
            line=dict(color=ORANGE, width=2.5),
            yaxis='y2',
        ))

    layout_opts = _base_layout(
        f"Gross Runs Attribution — {PADD_LABELS.get(padd, padd)}",
        yaxis_title="Crude % of Gross",
    )
    layout_opts['yaxis'] = dict(title="Crude % of Gross", color=RED)
    layout_opts['yaxis2'] = dict(
        title="Feedstock % of Gross", overlaying='y', side='right',
        color=ORANGE, showgrid=False,
    )
    layout_opts['margin'] = dict(l=60, r=60, t=70, b=35)
    fig.update_layout(**layout_opts)
    return fig


# ── Statistics helpers ────────────────────────────────────────────────

def _compute_stats(dates, values):
    """Compute statistical metrics for a time series."""
    if not values or len(values) < 2:
        return None
    s = pd.Series(values, index=dates)
    current = s.iloc[-1]

    avg_4 = s.rolling(4, min_periods=1).mean().iloc[-1]
    avg_52 = s.rolling(52, min_periods=1).mean().iloc[-1] if len(s) >= 10 else current

    mean_12 = s.rolling(12, min_periods=4).mean().iloc[-1]
    std_12 = s.rolling(12, min_periods=4).std().iloc[-1]
    zscore = (current - mean_12) / std_12 if std_12 and std_12 > 0 else 0.0

    percentile = (s <= current).sum() / len(s) * 100

    yoy = current - s.iloc[-53] if len(s) >= 53 else None

    if len(s) >= 12:
        x = np.arange(12, dtype=float)
        slope = float(np.polyfit(x, s.iloc[-12:].values, 1)[0])
    else:
        slope = None

    cv = (std_12 / mean_12 * 100) if mean_12 and mean_12 > 0 and std_12 else None

    return {
        'current': current,
        'avg_4': avg_4,
        'avg_52': avg_52,
        'zscore': zscore,
        'percentile': percentile,
        'yoy': yoy,
        'slope': slope,
        'cv': cv,
    }


def _zscore_color(z):
    """Return background color based on z-score magnitude."""
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


# 9. Z-Score & Anomaly Detection
@callback(
    Output("zscore-chart-p13", "figure"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_zscore_chart(data, padd):
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    row = get_series_row(df, series['crude_runs'])
    if row is None:
        return _empty_fig("Crude runs data not available")

    dates, values = extract_time_series(row)
    if len(dates) < 12:
        return _empty_fig("Not enough data for z-score")

    s = pd.Series(values, index=dates)
    rolling_mean = s.rolling(12, min_periods=4).mean()
    rolling_std = s.rolling(12, min_periods=4).std()
    zscore = (s - rolling_mean) / rolling_std
    upper_band = rolling_mean + 2 * rolling_std
    lower_band = rolling_mean - 2 * rolling_std

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.6, 0.4], vertical_spacing=0.08,
        subplot_titles=[
            f"Crude Runs with Confidence Band — {PADD_LABELS.get(padd, padd)}",
            "Z-Score (12-Week Rolling)"
        ],
    )

    # Top: confidence band
    fig.add_trace(go.Scatter(
        x=dates, y=upper_band, mode='lines', name='Upper Band (+2σ)',
        line=dict(width=0), showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=lower_band, mode='lines', name='Confidence Band (±2σ)',
        line=dict(width=0), fill='tonexty',
        fillcolor='rgba(0,173,239,0.12)',
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode='lines', name='Crude Runs',
        line=dict(color=RED, width=2),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=rolling_mean, mode='lines', name='12wk Mean',
        line=dict(color=GRAY_300, width=1.5, dash='dash'),
    ), row=1, col=1)

    # Bottom: z-score
    fig.add_hrect(y0=-1, y1=1, fillcolor="rgba(74,176,77,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=1, y1=2, fillcolor="rgba(246,142,47,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=-2, y1=-1, fillcolor="rgba(246,142,47,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=2, y1=4, fillcolor="rgba(236,0,43,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=-4, y1=-2, fillcolor="rgba(236,0,43,0.08)", line_width=0, row=2, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=zscore, mode='lines', name='Z-Score',
        line=dict(color=BLUE, width=2),
    ), row=2, col=1)

    # Anomaly markers (fillna guards against NaN from rolling warmup)
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
        height=420,
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=60, r=20, t=50, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode='x unified',
    )
    fig.update_yaxes(title_text="kbd", row=1, col=1)
    fig.update_yaxes(title_text="z-score", row=2, col=1)

    # Color subplot titles red
    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=14, color=RED)

    return fig


# 10. Stats Summary Table
@callback(
    Output("stats-summary-p13", "children"),
    [Input("current-data-store-p13", "data"),
     Input("padd-selector-p13", "value")]
)
def update_stats_summary(data, padd):
    if not data:
        return html.Div("No data available")
    df = pd.DataFrame(data)
    series = PADD_SERIES.get(padd, PADD_SERIES['US'])

    # Prepare 5 series
    columns = {}
    kbd_cols = set()

    for key, label in [('crude_runs', 'Crude'), ('gross_runs', 'Gross'), ('feedstock_runs', 'Feedstock')]:
        row = get_series_row(df, series[key])
        if row is not None:
            d, v = extract_time_series(row)
            columns[label] = _compute_stats(d, v)
            kbd_cols.add(label)

    row = get_series_row(df, series['utilization'])
    if row is not None:
        d, v = extract_time_series(row)
        columns['Util %'] = _compute_stats(d, v)

    imp_row = get_series_row(df, series['crude_imports'])
    run_row = get_series_row(df, series['crude_runs'])
    if imp_row is not None and run_row is not None:
        imp_d, imp_v = extract_time_series(imp_row)
        run_d, run_v = extract_time_series(run_row)
        ratio_d, ratio_v = compute_ratio_series(imp_d, imp_v, run_d, run_v)
        columns['Imp %'] = _compute_stats(ratio_d, ratio_v)

    if not columns:
        return html.Div("No data available for statistics")

    col_names = list(columns.keys())

    metric_rows = [
        ('Current', 'current', lambda v, cn: _fmt(v, ",.0f") if cn in kbd_cols else _fmt(v, ".1f", "%")),
        ('4wk Avg', 'avg_4', lambda v, cn: _fmt(v, ",.0f") if cn in kbd_cols else _fmt(v, ".1f", "%")),
        ('52wk Avg', 'avg_52', lambda v, cn: _fmt(v, ",.0f") if cn in kbd_cols else _fmt(v, ".1f", "%")),
        ('Z-Score (12wk)', 'zscore', lambda v, cn: _fmt(v, "+.2f")),
        ('Percentile', 'percentile', lambda v, cn: _fmt(v, ".0f", "th")),
        ('YoY Change', 'yoy', lambda v, cn: _fmt(v, "+,.0f") if cn in kbd_cols else _fmt(v, "+.1f", " ppt")),
        ('Trend (12wk)', 'slope', lambda v, cn: _fmt(v, "+,.1f", "/wk") if cn in kbd_cols else _fmt(v, "+.2f", "/wk")),
        ('Volatility (CV)', 'cv', lambda v, cn: _fmt(v, ".1f", "%")),
    ]

    # Header
    header = html.Tr(
        [html.Th("Metric", style={"padding": "8px 10px", "textAlign": "left", "borderBottom": f"2px solid {RED}",
                                   "color": RED, "fontWeight": "700", "fontSize": "0.85em"})] +
        [html.Th(cn, style={"padding": "8px 10px", "textAlign": "right", "borderBottom": f"2px solid {RED}",
                            "color": RED, "fontWeight": "700", "fontSize": "0.85em"}) for cn in col_names]
    )

    rows = []
    for i, (label, key, formatter) in enumerate(metric_rows):
        bg = "white" if i % 2 == 0 else GRAY_50
        cells = [html.Td(label, style={
            "padding": "7px 10px", "fontWeight": "600", "fontSize": "0.85em", "color": GRAY_500,
        })]
        for cn in col_names:
            stats = columns.get(cn)
            val = stats[key] if stats else None
            cell_style = {
                "padding": "7px 10px", "textAlign": "right",
                "fontWeight": "700", "fontSize": "0.9em",
            }
            # Color-code z-score cells
            if key == 'zscore' and val is not None:
                cell_style["color"] = "white"
                cell_style["backgroundColor"] = _zscore_color(val)
                cell_style["borderRadius"] = "4px"
            # Color-code YoY and trend
            elif key in ('yoy', 'slope') and val is not None:
                cell_style["color"] = POSITIVE if val >= 0 else NEGATIVE
            else:
                cell_style["color"] = BLACK

            cells.append(html.Td(formatter(val, cn), style=cell_style))
        rows.append(html.Tr(cells, style={"backgroundColor": bg}))

    title = html.Div(
        f"Statistics Summary — {PADD_LABELS.get(padd, padd)}",
        style={"fontSize": "15px", "fontWeight": "700", "color": RED, "marginBottom": "10px"},
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
