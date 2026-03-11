from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.utils.data_loader import loader
from src.utils.colors import (
    COLORSCALE_EFFICIENCY,
    RED, BLUE, GREEN, ORANGE, PURPLE,
    GRAY_50, GRAY_200, GRAY_500, GRAY_800,
    POSITIVE, NEGATIVE,
)

# ── Data Loading ──────────────────────────────────────────────────────────────

df = loader.load_steo_dpr_data()
mapping_df = loader.load_dpr_mapping()

metadata_cols = ['id', 'name', 'release_date', 'uom']
date_columns = [col for col in df.columns if col not in metadata_cols]

df_melted = pd.melt(df, id_vars=metadata_cols, value_vars=date_columns,
                    var_name='delivery_month', value_name='value')
df_melted['delivery_month'] = pd.to_datetime(df_melted['delivery_month'])
df_melted = df_melted.merge(mapping_df[['id', 'region']], on='id', how='left')

release_dates = sorted(df_melted['release_date'].unique(), reverse=True)

# ── Constants ─────────────────────────────────────────────────────────────────

REGIONS_ORDER = ['Permian', 'Bakken', 'Eagle Ford', 'Appalachia', 'Haynesville', 'Rest of L48 ex GOM']
REGION_ABBREVS = {
    'Permian': 'PM', 'Bakken': 'BK', 'Eagle Ford': 'EF',
    'Appalachia': 'AP', 'Haynesville': 'HA', 'Rest of L48 ex GOM': 'R48',
}
REGION_COLORS = {
    'Permian': BLUE, 'Bakken': RED, 'Eagle Ford': GREEN,
    'Appalachia': ORANGE, 'Haynesville': PURPLE, 'Rest of L48 ex GOM': GRAY_500,
}

# label, unit shown in KPI/table, Python format string, scale multiplier
METRIC_CONFIG = {
    'production_per_rig': {'label': 'Production / Rig', 'unit': 'kbd/rig', 'fmt': ',.1f', 'scale': 1000},
    'wells_per_rig':      {'label': 'Wells / Rig',      'unit': 'wells',   'fmt': '.2f',  'scale': 1},
    'completion_rate':     {'label': 'Completion Rate',  'unit': '%',       'fmt': '.0f',  'scale': 100},
    'duc_ratio':           {'label': 'DUC Ratio',        'unit': 'x',      'fmt': '.1f',  'scale': 1},
}

TIME_RANGES = {
    '12m': 12,
    '24m': 24,
    '36m': 36,
    'All': None,
}

CHART_HEIGHT = 650
PAGE_STYLE = {"padding": "2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"}

# ── Calculation ───────────────────────────────────────────────────────────────

def calculate_efficiency_metrics(df_melted, release_date):
    """Calculate efficiency metrics by region and time, dropping NaN rows."""
    df_filtered = df_melted[df_melted['release_date'] == release_date].copy()

    pivot_data = df_filtered.pivot_table(
        index=['delivery_month', 'region'], columns='id',
        values='value', aggfunc='first'
    ).reset_index()

    efficiency_metrics = []
    for _, row in pivot_data.iterrows():
        region = row['region']
        month = row['delivery_month']

        if pd.isna(region) or region not in REGIONS_ORDER:
            continue

        abbr = REGION_ABBREVS.get(region, '')
        if not abbr:
            continue

        production = row.get(f'COPR{abbr}', np.nan)
        rigs = row.get(f'RIGS{abbr}', np.nan)
        wells_drilled = row.get(f'NWD{abbr}', np.nan)
        wells_completed = row.get(f'NWC{abbr}', np.nan)
        ducs = row.get(f'DUCS{abbr}', np.nan)

        # Skip rows where rig count is missing — can't compute efficiency
        if pd.isna(rigs) or rigs == 0:
            continue
        if pd.isna(production):
            continue

        wells_drilled = wells_drilled if pd.notna(wells_drilled) else 0
        wells_completed = wells_completed if pd.notna(wells_completed) else 0
        ducs = ducs if pd.notna(ducs) else 0

        prod_per_rig = production / rigs
        wells_per_rig = wells_drilled / rigs
        completion_rate = wells_completed / wells_drilled if wells_drilled > 0 else 0
        duc_ratio = ducs / wells_drilled if wells_drilled > 0 else 0

        efficiency_metrics.append({
            'region': region, 'month': month,
            'production_per_rig': prod_per_rig,
            'wells_per_rig': wells_per_rig,
            'completion_rate': completion_rate,
            'duc_ratio': duc_ratio,
            'total_production': production,
            'total_rigs': rigs,
        })

    return pd.DataFrame(efficiency_metrics)

# ── Formatting ────────────────────────────────────────────────────────────────

def _format_value(val, metric):
    """Format a value for display, applying metric-specific scale."""
    if pd.isna(val):
        return '—'
    cfg = METRIC_CONFIG[metric]
    scaled = val * cfg['scale']
    formatted = f'{scaled:{cfg["fmt"]}}'
    if cfg['unit'] == '%':
        formatted += '%'
    elif cfg['unit'] == 'x':
        formatted += 'x'
    return formatted


def _format_cell(val, metric):
    """Compact cell format for heatmap annotations."""
    if pd.isna(val):
        return ''
    cfg = METRIC_CONFIG[metric]
    scaled = val * cfg['scale']
    # Compact: no unit suffix, just the number
    return f'{scaled:{cfg["fmt"]}}'

# ── Heatmap Figure ────────────────────────────────────────────────────────────

def create_efficiency_heatmap(efficiency_df, metric='production_per_rig',
                               use_zscore=False, n_months=24):
    """Create a premium heatmap for efficiency metrics."""
    if efficiency_df.empty:
        return go.Figure()

    cfg = METRIC_CONFIG[metric]
    work_df = efficiency_df.copy()

    # Limit to last N months
    if n_months is not None:
        cutoff = work_df['month'].max() - pd.DateOffset(months=n_months)
        work_df = work_df[work_df['month'] >= cutoff]

    if work_df.empty:
        return go.Figure()

    # Pivot: regions on y, months on x
    heatmap_data = work_df.pivot_table(
        index='region', columns='month', values=metric, aggfunc='mean'
    )
    ordered_regions = [r for r in REGIONS_ORDER if r in heatmap_data.index]
    heatmap_data = heatmap_data.loc[ordered_regions]

    # Apply display scale for z-values (so colorbar shows meaningful numbers)
    z_values = heatmap_data.values.copy().astype(float) * cfg['scale']
    x_labels = [d.strftime('%b %Y') for d in heatmap_data.columns]
    y_labels = list(heatmap_data.index)
    n_cols = len(x_labels)

    # Text annotations — only show if cells are wide enough
    show_text = n_cols <= 36
    text_size = 12 if n_cols <= 12 else 11 if n_cols <= 18 else 9 if n_cols <= 30 else 7
    text_data = None
    if show_text:
        text_data = []
        for row in heatmap_data.values:
            text_data.append([_format_cell(v, metric) for v in row])

    # Compute MoM changes for hover (on scaled values)
    mom_change = np.full_like(z_values, np.nan)
    if z_values.shape[1] > 1:
        mom_change[:, 1:] = z_values[:, 1:] - z_values[:, :-1]

    mom_pct = np.full_like(z_values, np.nan)
    with np.errstate(divide='ignore', invalid='ignore'):
        if z_values.shape[1] > 1:
            prev = z_values[:, :-1]
            mask = (prev != 0) & ~np.isnan(prev)
            pct = np.where(mask, (z_values[:, 1:] - prev) / np.abs(prev) * 100, np.nan)
            mom_pct[:, 1:] = pct

    # Z-score normalization (per region row)
    colorbar_title = f'{cfg["label"]} ({cfg["unit"]})'
    if use_zscore:
        for i in range(z_values.shape[0]):
            row_mean = np.nanmean(z_values[i])
            row_std = np.nanstd(z_values[i])
            z_values[i] = (z_values[i] - row_mean) / row_std if row_std > 0 else 0
        colorbar_title = 'Z-Score (σ)'
        # Override text with z-score values
        if show_text:
            text_data = []
            for row in z_values:
                text_data.append([f'{v:+.1f}σ' if not np.isnan(v) else '' for v in row])

    # Round customdata so hover displays clean numbers
    mom_change_rounded = np.round(mom_change, 1)
    mom_pct_rounded = np.round(mom_pct, 1)
    customdata = np.stack([mom_change_rounded, mom_pct_rounded], axis=-1)

    heatmap_trace = go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale=COLORSCALE_EFFICIENCY,
        xgap=4,
        ygap=4,
        hoverongaps=False,
        customdata=customdata,
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Month: %{x}<br>'
            f'{cfg["label"]}: %{{z:{cfg["fmt"]}}} {cfg["unit"]}<br>'
            'MoM: %{customdata[0]:+.1f}<br>'
            'MoM %: %{customdata[1]:+.1f}%'
            '<extra></extra>'
        ),
        colorbar=dict(
            title=dict(text=colorbar_title, side='right', font=dict(size=12, family='Montserrat')),
            thickness=18, len=0.85, outlinewidth=0,
            tickfont=dict(size=11, family='Montserrat'),
        ),
    )

    if show_text and text_data:
        heatmap_trace.text = text_data
        heatmap_trace.texttemplate = '<b>%{text}</b>'
        heatmap_trace.textfont = dict(size=text_size, family='Montserrat', color='#1a1a2e')

    fig = go.Figure(data=heatmap_trace)

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Montserrat', color=GRAY_800),
        height=CHART_HEIGHT,
        margin=dict(l=160, r=60, t=20, b=80),
        xaxis=dict(
            side='bottom', tickangle=-45,
            tickfont=dict(size=11, family='Montserrat'),
            dtick=max(1, n_cols // 12),  # Fewer ticks, more readable
        ),
        yaxis=dict(
            autorange='reversed',
            tickfont=dict(size=13, family='Montserrat', color=GRAY_800),
        ),
    )

    return fig

# ── KPI Strip Builder ─────────────────────────────────────────────────────────

def _build_kpi_strip(efficiency_df, metric):
    """Build a row of 6 KPI cards showing latest month snapshot per region."""
    if efficiency_df.empty:
        return html.Div()

    latest_month = efficiency_df['month'].max()
    months_sorted = sorted(efficiency_df['month'].unique())
    prev_month = None
    for m in months_sorted:
        if m < latest_month:
            prev_month = m

    cards = []
    for region in REGIONS_ORDER:
        region_df = efficiency_df[efficiency_df['region'] == region]
        latest = region_df[region_df['month'] == latest_month]
        color = REGION_COLORS.get(region, GRAY_500)

        if latest.empty:
            cards.append(dbc.Col(html.Div(), lg=2, md=4, sm=6))
            continue

        val = latest[metric].iloc[0]
        val_str = _format_value(val, metric)

        # MoM delta
        delta_children = []
        if prev_month is not None:
            prev = region_df[region_df['month'] == prev_month]
            if not prev.empty:
                prev_val = prev[metric].iloc[0]
                delta = val - prev_val
                delta_color = POSITIVE if delta >= 0 else NEGATIVE
                arrow = '▲ ' if delta >= 0 else '▼ '
                delta_children = [
                    html.Span(arrow + _format_value(abs(delta), metric), style={
                        'fontSize': '0.8rem', 'fontWeight': '600', 'color': delta_color,
                    }),
                    html.Span(' m/m', style={
                        'fontSize': '0.72rem', 'color': GRAY_500, 'marginLeft': '3px',
                    }),
                ]

        # Short region label for display
        short_region = region.replace('Rest of L48 ex GOM', 'Rest of L48')

        card = dbc.Card(
            dbc.CardBody([
                html.Div(short_region, style={
                    'fontSize': '0.7rem', 'fontWeight': '700',
                    'letterSpacing': '0.08em', 'color': GRAY_500,
                    'textTransform': 'uppercase', 'marginBottom': '0.35rem',
                    'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis',
                }),
                html.Div(val_str, style={
                    'fontSize': '1.4rem', 'fontWeight': '700',
                    'color': GRAY_800, 'lineHeight': '1',
                    'fontFeatureSettings': "'tnum'", 'marginBottom': '0.3rem',
                }),
                html.Div(delta_children) if delta_children else html.Div(),
            ], style={'padding': '0.85rem 0.9rem'}),
            style={
                'borderLeft': f'3px solid {color}',
                'borderRadius': '4px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                'backgroundColor': 'white',
            },
        )
        cards.append(dbc.Col(card, lg=2, md=4, sm=6))

    return dbc.Row(cards, className='g-3')

# ── Summary Table Builder ─────────────────────────────────────────────────────

def _build_summary_table(efficiency_df, metric):
    """Build a styled summary table with per-region statistics."""
    if efficiency_df.empty:
        return html.Div("No data available.")

    latest_month = efficiency_df['month'].max()

    th_style = {
        'padding': '0.6rem 0.8rem', 'fontSize': '0.72rem', 'fontWeight': '700',
        'letterSpacing': '0.06em', 'textTransform': 'uppercase', 'color': GRAY_500,
        'borderBottom': f'2px solid {GRAY_200}',
    }

    header = html.Thead(html.Tr([
        html.Th('Region', style={**th_style, 'textAlign': 'left'}),
        html.Th('Latest', style={**th_style, 'textAlign': 'right'}),
        html.Th('Average', style={**th_style, 'textAlign': 'right'}),
        html.Th('Min', style={**th_style, 'textAlign': 'right'}),
        html.Th('Max', style={**th_style, 'textAlign': 'right'}),
        html.Th('Trend', style={**th_style, 'textAlign': 'center'}),
    ]))

    rows = []
    for i, region in enumerate(REGIONS_ORDER):
        region_df = efficiency_df[efficiency_df['region'] == region]
        if region_df.empty:
            continue

        vals = region_df[metric].dropna()
        if vals.empty:
            continue

        latest_val = region_df[region_df['month'] == latest_month][metric]
        latest_str = _format_value(latest_val.iloc[0], metric) if not latest_val.empty else '—'

        # Trend: compare last 3 months avg vs first 3 months avg
        sorted_vals = region_df.sort_values('month')[metric].dropna()
        n = len(sorted_vals)
        if n >= 6:
            trend_up = sorted_vals.iloc[-3:].mean() > sorted_vals.iloc[:3].mean()
        elif n >= 2:
            trend_up = sorted_vals.iloc[-1] > sorted_vals.iloc[0]
        else:
            trend_up = None

        if trend_up is None:
            trend_icon = html.Span('—', style={'color': GRAY_500})
        elif trend_up:
            trend_icon = html.Span('▲', style={'color': POSITIVE, 'fontSize': '0.85rem', 'fontWeight': '700'})
        else:
            trend_icon = html.Span('▼', style={'color': NEGATIVE, 'fontSize': '0.85rem', 'fontWeight': '700'})

        bg = 'white' if i % 2 == 0 else GRAY_50
        td = {'padding': '0.55rem 0.8rem', 'fontFeatureSettings': "'tnum'", 'fontSize': '0.88rem'}

        rows.append(html.Tr([
            html.Td(region, style={**td, 'textAlign': 'left', 'fontWeight': '600'}),
            html.Td(latest_str, style={**td, 'textAlign': 'right', 'fontWeight': '700', 'color': GRAY_800}),
            html.Td(_format_value(vals.mean(), metric), style={**td, 'textAlign': 'right'}),
            html.Td(_format_value(vals.min(), metric), style={**td, 'textAlign': 'right'}),
            html.Td(_format_value(vals.max(), metric), style={**td, 'textAlign': 'right'}),
            html.Td(trend_icon, style={**td, 'textAlign': 'center'}),
        ], style={'backgroundColor': bg, 'borderBottom': f'1px solid {GRAY_200}'}))

    return html.Table([header, html.Tbody(rows)], style={
        'width': '100%', 'borderCollapse': 'collapse',
        'fontFamily': 'Montserrat', 'color': GRAY_800,
    })

# ── Layout ────────────────────────────────────────────────────────────────────

layout = html.Div([
    # Page Hero
    html.Div([
        html.Div('DPR ANALYTICS', className='page-eyebrow'),
        html.H1('Efficiency Heatmap', className='page-title'),
        html.P(
            'Regional drilling efficiency across major U.S. basins — production per rig, '
            'completion rates, and DUC ratios over time.',
            className='page-summary',
        ),
    ], className='page-hero'),

    # Controls Row
    dbc.Row([
        # Release Date
        dbc.Col([
            html.Label('Release Date', style={
                'fontSize': '0.72rem', 'fontWeight': '700', 'letterSpacing': '0.06em',
                'textTransform': 'uppercase', 'color': GRAY_500, 'marginBottom': '0.35rem',
                'display': 'block',
            }),
            dcc.Dropdown(
                id='page3-7-release-dropdown',
                options=[{'label': d.strftime('%Y-%m-%d'), 'value': d.isoformat()} for d in release_dates],
                value=release_dates[0].isoformat() if release_dates else None,
                clearable=False,
                style={'fontFamily': 'Montserrat'},
            ),
        ], lg=2, md=3, sm=12),

        # Metric Selector (pill buttons)
        dbc.Col([
            html.Label('Metric', style={
                'fontSize': '0.72rem', 'fontWeight': '700', 'letterSpacing': '0.06em',
                'textTransform': 'uppercase', 'color': GRAY_500, 'marginBottom': '0.35rem',
                'display': 'block',
            }),
            dbc.RadioItems(
                id='page3-7-metric-selector',
                options=[
                    {'label': cfg['label'], 'value': key}
                    for key, cfg in METRIC_CONFIG.items()
                ],
                value='production_per_rig',
                inline=True,
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-primary btn-sm',
                labelCheckedClassName='active',
            ),
        ], lg=6, md=5, sm=12),

        # Time Range
        dbc.Col([
            html.Label('Time Range', style={
                'fontSize': '0.72rem', 'fontWeight': '700', 'letterSpacing': '0.06em',
                'textTransform': 'uppercase', 'color': GRAY_500, 'marginBottom': '0.35rem',
                'display': 'block',
            }),
            dbc.RadioItems(
                id='page3-7-range-selector',
                options=[{'label': k, 'value': str(v) if v else 'all'} for k, v in TIME_RANGES.items()],
                value='12',
                inline=True,
                className='btn-group',
                inputClassName='btn-check',
                labelClassName='btn btn-outline-secondary btn-sm',
                labelCheckedClassName='active',
            ),
        ], lg=2, md=2, sm=6),

        # Z-Score Toggle
        dbc.Col([
            html.Label('Normalize', style={
                'fontSize': '0.72rem', 'fontWeight': '700', 'letterSpacing': '0.06em',
                'textTransform': 'uppercase', 'color': GRAY_500, 'marginBottom': '0.35rem',
                'display': 'block',
            }),
            dbc.Switch(
                id='page3-7-zscore-toggle',
                label='Z-Score',
                value=False,
                style={'marginTop': '0.2rem'},
            ),
        ], lg=2, md=2, sm=6),
    ], className='g-3 align-items-end', style={'marginBottom': '1.5rem'}),

    # KPI Strip
    html.Div(id='page3-7-kpi-strip', style={'marginBottom': '1.5rem'}),

    # Heatmap Card
    dbc.Card([
        dbc.CardBody([
            dcc.Graph(
                id='page3-7-efficiency-heatmap',
                config={'displayModeBar': False},
            ),
        ], style={'padding': '1rem'}),
    ], className='surface-card', style={'marginBottom': '1.5rem'}),

    # Summary Table Card
    dbc.Card([
        dbc.CardBody([
            html.Div('REGIONAL SUMMARY', style={
                'fontSize': '0.72rem', 'fontWeight': '700', 'letterSpacing': '0.1em',
                'textTransform': 'uppercase', 'color': GRAY_500, 'marginBottom': '0.8rem',
            }),
            html.Div(id='page3-7-efficiency-summary'),
        ]),
    ], className='surface-card'),
], style=PAGE_STYLE)

# ── Callback ──────────────────────────────────────────────────────────────────

@callback(
    [Output('page3-7-efficiency-heatmap', 'figure'),
     Output('page3-7-efficiency-summary', 'children'),
     Output('page3-7-kpi-strip', 'children')],
    [Input('page3-7-release-dropdown', 'value'),
     Input('page3-7-metric-selector', 'value'),
     Input('page3-7-range-selector', 'value'),
     Input('page3-7-zscore-toggle', 'value')]
)
def update_efficiency_analysis(release_date_str, metric, time_range, use_zscore):
    if not release_date_str:
        return go.Figure(), '', html.Div()

    release_date = pd.to_datetime(release_date_str)
    efficiency_df = calculate_efficiency_metrics(df_melted, release_date)

    if efficiency_df.empty:
        return go.Figure(), 'No data available for selected parameters.', html.Div()

    n_months = int(time_range) if time_range != 'all' else None

    heatmap_fig = create_efficiency_heatmap(efficiency_df, metric, use_zscore, n_months)
    summary = _build_summary_table(efficiency_df, metric)
    kpi_strip = _build_kpi_strip(efficiency_df, metric)

    return heatmap_fig, summary, kpi_strip
