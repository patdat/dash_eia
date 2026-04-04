#######################################################################
### Cushing Page ######################################################

commodity = "Cushing "

idents = {
    "W_EPC0_SAX_YCUOK_MBBL": "Cushing Stocks (kb)",
    "WCESTUS1": "US Commercial Stocks (kb)",
    "WCESTP21": "P2 Commercial Stocks (kb)",
    "WCESTP31": "P3 Commercial Stocks (kb)",
}


def graph_sections_input(page_id):
    return [
        ("Stocks", [f"{page_id}-graph-1"]),
        ("Context", [f"{page_id}-graph-2", f"{page_id}-graph-3", f"{page_id}-graph-4"]),
    ]


### END MANUAL INPUTS #################################################
#######################################################################

from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

from src.app import app
from src.wps.calculation import create_callbacks, create_layout
from src.utils.data_loader import loader, get_line_data_for_ids
from src.utils.colors import (
    RED, BLUE, ORANGE, GREEN, POSITIVE, NEGATIVE,
    GRAY_50, GRAY_200, GRAY_500, GRAY_800, BLACK, WHITE
)
from pages.page1 import create_metric_card


# Page-specific variables
page_id = "page2_12"  # Internal ID preserved from original filename to avoid callback collisions
idents_list = list(idents.keys())
num_graphs = len(idents_list)


def build_cushing_kpis():
    """Build KPI metric cards for Cushing overview."""
    try:
        df = loader.load_wps_pivot_data()
        df['period'] = pd.to_datetime(df['period'])
        df_sorted = df.sort_values('period')
        latest = df_sorted.iloc[-1]
        previous = df_sorted.iloc[-2]

        # Cushing stocks (kb -> M bbl by dividing by 1000)
        cushing_current = latest.get('W_EPC0_SAX_YCUOK_MBBL', 0) / 1000
        cushing_previous = previous.get('W_EPC0_SAX_YCUOK_MBBL', 0) / 1000
        cushing_change_m = cushing_current - cushing_previous
        cushing_change_kb = cushing_change_m * 1000
        cushing_change_pct = (cushing_change_kb / (cushing_previous * 1000) * 100) if cushing_previous else 0

        # US Commercial stocks
        commercial_current = latest.get('WCESTUS1', 0) / 1000

        # Cushing as % of commercial
        pct_of_commercial = (cushing_current / commercial_current * 100) if commercial_current else 0

        # 5-year average
        recent_years = df_sorted[df_sorted['period'] >= pd.Timestamp.now() - pd.DateOffset(years=5)]
        cushing_5yr_avg = recent_years['W_EPC0_SAX_YCUOK_MBBL'].mean() / 1000 if not recent_years.empty else cushing_current
        vs_avg = cushing_current - cushing_5yr_avg
        vs_avg_pct = (vs_avg / cushing_5yr_avg * 100) if cushing_5yr_avg else 0

        # Historical avg ratio
        if not recent_years.empty:
            ratios = recent_years['W_EPC0_SAX_YCUOK_MBBL'] / recent_years['WCESTUS1'] * 100
            avg_ratio = ratios.mean()
        else:
            avg_ratio = pct_of_commercial

        return [
            dbc.Col([
                create_metric_card(
                    "CUSHING STOCKS",
                    f"{cushing_current:.1f} mb",
                    f"{'+' if cushing_change_m >= 0 else ''}{cushing_change_m:.1f} mb",
                    cushing_change_m >= 0,
                    RED
                )
            ], lg=3, md=6),
            dbc.Col([
                create_metric_card(
                    "WEEK/WEEK CHANGE",
                    f"{'+' if cushing_change_kb >= 0 else ''}{cushing_change_kb:,.0f} kb",
                    f"{'+' if cushing_change_pct >= 0 else ''}{cushing_change_pct:.1f}%",
                    cushing_change_kb >= 0,
                    POSITIVE if cushing_change_kb >= 0 else NEGATIVE
                )
            ], lg=3, md=6),
            dbc.Col([
                create_metric_card(
                    "VS 5-YEAR AVG",
                    f"{'+' if vs_avg >= 0 else ''}{vs_avg:.1f} mb",
                    f"{'+' if vs_avg_pct >= 0 else ''}{vs_avg_pct:.1f}%",
                    vs_avg >= 0,
                    BLUE
                )
            ], lg=3, md=6),
            dbc.Col([
                create_metric_card(
                    "% OF US COMMERCIAL",
                    f"{pct_of_commercial:.1f}%",
                    f"5yr avg: {avg_ratio:.1f}%",
                    pct_of_commercial >= avg_ratio,
                    ORANGE
                )
            ], lg=3, md=6),
        ]

    except Exception as e:
        print(f"Error loading Cushing metrics: {e}")
        return [
            dbc.Col([create_metric_card("CUSHING STOCKS", "—", "—", True, RED)], lg=3, md=6),
            dbc.Col([create_metric_card("WEEK/WEEK CHANGE", "—", "—", True, GRAY_500)], lg=3, md=6),
            dbc.Col([create_metric_card("VS 5-YEAR AVG", "—", "—", True, BLUE)], lg=3, md=6),
            dbc.Col([create_metric_card("% OF US COMMERCIAL", "—", "—", True, ORANGE)], lg=3, md=6),
        ]


# Build layout
layout = html.Div([
    # Hero section
    html.Div([
        html.Div("EIA WEEKLY PETROLEUM STATUS", className="page-eyebrow"),
        html.H1("Cushing Analysis", className="page-title"),
        html.P(
            "Cushing, OK crude oil storage hub — the WTI delivery point and key barometer of US crude market balance.",
            className="page-summary"
        ),
    ], className="page-hero", style={"marginBottom": "1.5rem"}),

    # KPI cards
    dbc.Row(build_cushing_kpis(), style={"marginBottom": "1.5rem"}),

    # Standard WPS chart section (controls + 4 charts)
    create_layout(page_id, commodity, graph_sections_input(page_id)),

    # Custom analytics section
    html.Div([
        html.H1("Cushing Derived Analytics", className="eia-weekly-header-title"),
        html.Div([
            html.Div(
                dcc.Graph(id='cushing-pct-commercial', style={"height": "600px"}),
                className="graph-container",
                style={"width": "700px", "display": "inline-block", "verticalAlign": "top"}
            ),
            html.Div(
                dcc.Graph(id='cushing-weekly-change', style={"height": "600px"}),
                className="graph-container",
                style={"width": "700px", "display": "inline-block", "verticalAlign": "top", "marginLeft": "20px"}
            ),
        ], className="eia-weekly-graph-container",
           style={"display": "flex", "gridTemplateColumns": "1fr 1fr", "width": "1440px"}),
    ], style={"marginTop": "20px"}),

    # Advanced statistics section
    html.Div([
        html.H1("Cushing Advanced Statistics", className="eia-weekly-header-title"),
        html.Div([
            html.Div(
                dcc.Graph(id='cushing-zscore', style={"height": "600px"}),
                className="graph-container",
                style={"width": "700px", "display": "inline-block", "verticalAlign": "top"}
            ),
            html.Div(
                dcc.Graph(id='cushing-seasonal-deviation', style={"height": "600px"}),
                className="graph-container",
                style={"width": "700px", "display": "inline-block", "verticalAlign": "top", "marginLeft": "20px"}
            ),
            html.Div(
                dcc.Graph(id='cushing-percentile', style={"height": "600px"}),
                className="graph-container",
                style={"width": "700px", "display": "inline-block", "verticalAlign": "top", "marginLeft": "20px"}
            ),
        ], className="eia-weekly-graph-container",
           style={"display": "flex", "gridTemplateColumns": "1fr 1fr 1fr", "width": "2160px"}),
    ], style={"marginTop": "20px"}),

], style={"padding": "2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"})


# Register standard WPS callbacks for the 4 charts
create_callbacks(app, page_id, num_graphs, idents_list)


# Series for ratio chart: Cushing, P9 (P2+P3+P4), P2, P3
RATIO_SERIES = ('W_EPC0_SAX_YCUOK_MBBL', 'crudeStocksP9', 'WCESTP21', 'WCESTP31')
RATIO_CONFIG = [
    {'denom': 'crudeStocksP9', 'name': '% of P9 (P2+P3+P4)', 'color': RED},
    {'denom': 'WCESTP21',      'name': '% of PADD 2',         'color': BLUE},
    {'denom': 'WCESTP31',      'name': '% of PADD 3',         'color': ORANGE},
]


# Custom callback for Cushing as % of regional stocks
@callback(
    Output('cushing-pct-commercial', 'figure'),
    [Input(f"{page_id}-btn_1m-state", "data"),
     Input(f"{page_id}-btn_3m-state", "data"),
     Input(f"{page_id}-btn_12m-state", "data"),
     Input(f"{page_id}-btn_36m-state", "data"),
     Input(f"{page_id}-btn_60m-state", "data")]
)
def update_ratio_chart(btn_1m, btn_3m, btn_12m, btn_36m, btn_60m):
    df = get_line_data_for_ids(RATIO_SERIES)
    df = df.dropna(subset=list(RATIO_SERIES))

    # Apply time filter
    if btn_1m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=1)]
    elif btn_3m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=3)]
    elif btn_12m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=1)]
    elif btn_36m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=3)]
    elif btn_60m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=5)]

    cushing_col = 'W_EPC0_SAX_YCUOK_MBBL'
    fig = go.Figure()

    for cfg in RATIO_CONFIG:
        ratio = (df[cushing_col] / df[cfg['denom']]) * 100
        fig.add_trace(go.Scatter(
            x=df['period'],
            y=ratio,
            mode='lines',
            name=cfg['name'],
            line=dict(color=cfg['color'], width=1.5),
            hoverinfo='text',
            text=[f"{d.strftime('%m/%d/%y')}: {v:.1f}%" for d, v in zip(df['period'], ratio)],
        ))

    fig.update_layout(
        title=dict(
            text="Cushing as % of Regional Crude Stocks",
            y=0.95, x=0.05, xanchor='left', yanchor='top',
            font=dict(color=BLACK)
        ),
        height=600,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        hovermode='x unified',
        legend=dict(
            orientation='h', yanchor='top', y=0.98,
            xanchor='right', x=1,
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date',
            showline=True, linecolor=BLACK,
            gridcolor=WHITE,
            spikedash='dot', spikecolor=GREEN,
            spikethickness=1, showspikes=True,
        ),
        yaxis=dict(
            showline=True, linecolor=BLACK,
            gridcolor=WHITE,
            spikedash='dot', spikecolor=GREEN,
            spikethickness=1, showspikes=True,
            automargin=True, autorange=True,
            ticksuffix='%',
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Montserrat",
            bordercolor="#ccc"
        ),
        margin=dict(l=40, r=40, t=75, b=25),
    )

    return fig


# Custom callback for weekly inventory changes
@callback(
    Output('cushing-weekly-change', 'figure'),
    [Input(f"{page_id}-btn_1m-state", "data"),
     Input(f"{page_id}-btn_3m-state", "data"),
     Input(f"{page_id}-btn_12m-state", "data"),
     Input(f"{page_id}-btn_36m-state", "data"),
     Input(f"{page_id}-btn_60m-state", "data")]
)
def update_weekly_change_chart(btn_1m, btn_3m, btn_12m, btn_36m, btn_60m):
    df = get_line_data_for_ids(('W_EPC0_SAX_YCUOK_MBBL',))
    df = df.dropna(subset=['W_EPC0_SAX_YCUOK_MBBL'])
    df = df.sort_values('period')

    # Compute weekly change (line data is in mb, multiply by 1000 for kb)
    df['change'] = (df['W_EPC0_SAX_YCUOK_MBBL'].diff() * 1000).round(0)
    df = df.dropna(subset=['change'])

    # 4-week moving average of changes
    df['change_ma4'] = df['change'].rolling(window=4, min_periods=1).mean().round(0)

    # Apply time filter
    if btn_1m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=1)]
    elif btn_3m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=3)]
    elif btn_12m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=1)]
    elif btn_36m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=3)]
    elif btn_60m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=5)]

    last_change = df['change'].iloc[-1]
    colors = [POSITIVE if c >= 0 else NEGATIVE for c in df['change']]

    fig = go.Figure()

    # Weekly change bars
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['change'],
        marker_color=colors,
        name='Weekly Change',
        hoverinfo='text',
        hoverlabel=dict(bgcolor=RED, font=dict(color=WHITE)),
        text=[f"{d.strftime('%m/%d/%y')}: {v:+,.0f} kb" for d, v in zip(df['period'], df['change'])],
        showlegend=False,
    ))

    # 4-week MA overlay
    fig.add_trace(go.Scatter(
        x=df['period'],
        y=df['change_ma4'],
        mode='lines',
        line=dict(color=BLUE, width=2),
        name='4-week MA',
        hoverinfo='skip',
        showlegend=True,
    ))

    fig.update_layout(
        title=dict(
            text="Cushing Weekly Inventory Change (kb)",
            y=0.95, x=0.05, xanchor='left', yanchor='top',
            font=dict(color=BLACK)
        ),
        height=600,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1,
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date',
            showline=True, linecolor=BLACK,
            gridcolor=WHITE,
            spikedash='dot', spikecolor=GREEN,
            spikethickness=1, showspikes=True,
        ),
        yaxis=dict(
            showline=True, linecolor=BLACK,
            gridcolor=WHITE,
            spikedash='dot', spikecolor=GREEN,
            spikethickness=1, showspikes=True,
            automargin=True, autorange=True,
        ),
        shapes=[
            dict(
                type='line',
                x0=df['period'].min(), y0=0,
                x1=df['period'].max(), y1=0,
                line=dict(color=BLACK, width=0.5),
                xref='x', yref='y'
            ),
            dict(
                type='line',
                x0=df['period'].min(), y0=last_change,
                x1=df['period'].max(), y1=last_change,
                line=dict(color=GREEN, width=1, dash='dot'),
                xref='x', yref='y'
            ),
        ],
        annotations=[
            dict(
                xref='paper', yref='y',
                x=0, y=last_change,
                text=f"{last_change:+,.0f}",
                showarrow=False,
                bgcolor=GREEN, font=dict(color=WHITE),
                xanchor='right'
            ),
        ],
        margin=dict(l=40, r=40, t=75, b=25),
    )

    return fig


def _apply_time_filter(df, btn_1m, btn_3m, btn_12m, btn_36m, btn_60m):
    """Apply time range filter based on button states."""
    if btn_1m:
        return df[df['period'] >= df['period'].max() - pd.DateOffset(months=1)]
    elif btn_3m:
        return df[df['period'] >= df['period'].max() - pd.DateOffset(months=3)]
    elif btn_12m:
        return df[df['period'] >= df['period'].max() - pd.DateOffset(years=1)]
    elif btn_36m:
        return df[df['period'] >= df['period'].max() - pd.DateOffset(years=3)]
    elif btn_60m:
        return df[df['period'] >= df['period'].max() - pd.DateOffset(years=5)]
    return df


_TIME_INPUTS = [
    Input(f"{page_id}-btn_1m-state", "data"),
    Input(f"{page_id}-btn_3m-state", "data"),
    Input(f"{page_id}-btn_12m-state", "data"),
    Input(f"{page_id}-btn_36m-state", "data"),
    Input(f"{page_id}-btn_60m-state", "data"),
]


# Z-Score chart
@callback(Output('cushing-zscore', 'figure'), _TIME_INPUTS)
def update_zscore_chart(btn_1m, btn_3m, btn_12m, btn_36m, btn_60m):
    df = get_line_data_for_ids(('W_EPC0_SAX_YCUOK_MBBL',))
    df = df.dropna(subset=['W_EPC0_SAX_YCUOK_MBBL']).sort_values('period')

    col = 'W_EPC0_SAX_YCUOK_MBBL'
    window = 156  # ~3 years of weekly data
    df['rolling_mean'] = df[col].rolling(window=window, min_periods=52).mean()
    df['rolling_std'] = df[col].rolling(window=window, min_periods=52).std()
    df['zscore'] = (df[col] - df['rolling_mean']) / df['rolling_std']
    df = df.dropna(subset=['zscore'])

    df = _apply_time_filter(df, btn_1m, btn_3m, btn_12m, btn_36m, btn_60m)

    last_z = df['zscore'].iloc[-1]
    colors = [RED if z > 0 else BLUE for z in df['zscore']]

    fig = go.Figure()

    # Sigma bands
    for sigma, opacity in [(2, 0.06), (1, 0.10)]:
        fig.add_hrect(y0=-sigma, y1=sigma, fillcolor=BLUE, opacity=opacity, line_width=0)

    fig.add_trace(go.Bar(
        x=df['period'], y=df['zscore'],
        marker_color=colors, name='Z-Score',
        hoverinfo='text', showlegend=False,
        text=[f"{d.strftime('%m/%d/%y')}: {v:+.2f}σ" for d, v in zip(df['period'], df['zscore'])],
    ))

    # Reference lines
    for sigma in [-2, -1, 0, 1, 2]:
        fig.add_hline(y=sigma, line=dict(color=GRAY_500, width=0.5, dash='dash'))

    fig.add_annotation(
        xref='paper', yref='y', x=0.98, y=last_z,
        text=f"{last_z:+.2f}σ", showarrow=False,
        bgcolor=RED if last_z > 0 else BLUE, font=dict(color=WHITE, size=11),
        xanchor='right', borderpad=3,
    )

    fig.update_layout(
        title=dict(text="Cushing Z-Score (3yr Rolling)", y=0.95, x=0.05, xanchor='left', yanchor='top', font=dict(color=BLACK)),
        height=600, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Montserrat", bordercolor="#ccc"),
        xaxis=dict(showline=True, linecolor=BLACK, gridcolor=WHITE, spikedash='dot', spikecolor=GREEN, spikethickness=1, showspikes=True),
        yaxis=dict(showline=True, linecolor=BLACK, gridcolor=WHITE, zeroline=False, automargin=True),
        margin=dict(l=40, r=60, t=75, b=25),
    )
    return fig


# Seasonal Deviation chart
@callback(Output('cushing-seasonal-deviation', 'figure'), _TIME_INPUTS)
def update_seasonal_deviation_chart(btn_1m, btn_3m, btn_12m, btn_36m, btn_60m):
    df = get_line_data_for_ids(('W_EPC0_SAX_YCUOK_MBBL',))
    df = df.dropna(subset=['W_EPC0_SAX_YCUOK_MBBL']).sort_values('period')

    col = 'W_EPC0_SAX_YCUOK_MBBL'
    df['week'] = df['period'].dt.isocalendar().week.astype(int)

    # 5-year seasonal average
    cutoff = df['period'].max() - pd.DateOffset(years=5)
    hist = df[df['period'] >= cutoff]
    seasonal_avg = hist.groupby('week')[col].mean()

    df['seasonal_avg'] = df['week'].map(seasonal_avg)
    df['deviation'] = (df[col] - df['seasonal_avg']) * 1000  # kb
    df = df.dropna(subset=['deviation'])

    df = _apply_time_filter(df, btn_1m, btn_3m, btn_12m, btn_36m, btn_60m)

    last_dev = df['deviation'].iloc[-1]
    colors = [POSITIVE if d >= 0 else NEGATIVE for d in df['deviation']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['period'], y=df['deviation'],
        marker_color=colors, name='Deviation',
        hoverinfo='text', showlegend=False,
        text=[f"{d.strftime('%m/%d/%y')}: {v:+,.0f} kb" for d, v in zip(df['period'], df['deviation'])],
    ))

    fig.add_hline(y=0, line=dict(color=BLACK, width=0.5))

    fig.add_annotation(
        xref='paper', yref='y', x=0.98, y=last_dev,
        text=f"{last_dev:+,.0f} kb", showarrow=False,
        bgcolor=POSITIVE if last_dev >= 0 else NEGATIVE, font=dict(color=WHITE, size=11),
        xanchor='right', borderpad=3,
    )

    fig.update_layout(
        title=dict(text="Cushing vs Seasonal Average (kb)", y=0.95, x=0.05, xanchor='left', yanchor='top', font=dict(color=BLACK)),
        height=600, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Montserrat", bordercolor="#ccc"),
        xaxis=dict(showline=True, linecolor=BLACK, gridcolor=WHITE, spikedash='dot', spikecolor=GREEN, spikethickness=1, showspikes=True),
        yaxis=dict(showline=True, linecolor=BLACK, gridcolor=WHITE, zeroline=False, automargin=True),
        margin=dict(l=40, r=60, t=75, b=25),
    )
    return fig


# Percentile Rank chart
@callback(Output('cushing-percentile', 'figure'), _TIME_INPUTS)
def update_percentile_chart(btn_1m, btn_3m, btn_12m, btn_36m, btn_60m):
    df = get_line_data_for_ids(('W_EPC0_SAX_YCUOK_MBBL',))
    df = df.dropna(subset=['W_EPC0_SAX_YCUOK_MBBL']).sort_values('period')

    col = 'W_EPC0_SAX_YCUOK_MBBL'
    window = 156  # 3 years
    df['percentile'] = df[col].rolling(window=window, min_periods=52).apply(
        lambda x: (x.iloc[-1] >= x).sum() / len(x) * 100, raw=False
    )
    df = df.dropna(subset=['percentile'])

    df = _apply_time_filter(df, btn_1m, btn_3m, btn_12m, btn_36m, btn_60m)

    last_pct = df['percentile'].iloc[-1]

    fig = go.Figure()

    # Shaded zones
    fig.add_hrect(y0=0, y1=20, fillcolor=RED, opacity=0.08, line_width=0, annotation_text="Tight", annotation_position="top left")
    fig.add_hrect(y0=80, y1=100, fillcolor=GREEN, opacity=0.08, line_width=0, annotation_text="Loose", annotation_position="bottom left")

    fig.add_trace(go.Scatter(
        x=df['period'], y=df['percentile'],
        mode='lines', line=dict(color=BLACK, width=1.5),
        name='Percentile', showlegend=False,
        hoverinfo='text',
        text=[f"{d.strftime('%m/%d/%y')}: {v:.0f}th pctile" for d, v in zip(df['period'], df['percentile'])],
    ))

    # Reference lines
    fig.add_hline(y=50, line=dict(color=GRAY_500, width=0.5, dash='dash'))
    fig.add_hline(y=20, line=dict(color=RED, width=0.5, dash='dot'))
    fig.add_hline(y=80, line=dict(color=GREEN, width=0.5, dash='dot'))

    fig.add_annotation(
        xref='paper', yref='y', x=0.98, y=last_pct,
        text=f"{last_pct:.0f}th",
        showarrow=False,
        bgcolor=RED if last_pct < 20 else (GREEN if last_pct > 80 else BLACK),
        font=dict(color=WHITE, size=11), xanchor='right', borderpad=3,
    )

    fig.update_layout(
        title=dict(text="Cushing Percentile Rank (3yr Rolling)", y=0.95, x=0.05, xanchor='left', yanchor='top', font=dict(color=BLACK)),
        height=600, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Montserrat", bordercolor="#ccc"),
        xaxis=dict(showline=True, linecolor=BLACK, gridcolor=WHITE, spikedash='dot', spikecolor=GREEN, spikethickness=1, showspikes=True),
        yaxis=dict(showline=True, linecolor=BLACK, gridcolor=WHITE, range=[0, 100], ticksuffix='%', automargin=True),
        margin=dict(l=40, r=60, t=75, b=25),
    )
    return fig
