from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats as scipy_stats
from src.utils.data_loader import loader
from src.utils.colors import (
    RED, BLUE, BLACK, GREEN, ORANGE, PURPLE,
    GRAY_50, GRAY_200, GRAY_300, GRAY_500, GRAY_800,
    POSITIVE, NEGATIVE, COLORSCALE_EFFICIENCY,
)

# ── Data Loading ─────────────────────────────────────────────────────────────

df_melted_dpr = loader.load_processed_dpr_data(region=None)
mapping_dpr = loader.load_dpr_mapping()
RELEASES = sorted(df_melted_dpr['release_date'].unique(), reverse=True)
LATEST_RELEASE = RELEASES[0]

REGIONS = ['Permian', 'Bakken', 'Eagle Ford', 'Appalachia', 'Haynesville', 'Rest of L48 ex GOM']
REGION_COLORS = {
    'Permian': BLUE, 'Bakken': RED, 'Eagle Ford': GREEN,
    'Appalachia': ORANGE, 'Haynesville': PURPLE, 'Rest of L48 ex GOM': GRAY_500,
}

# Metric name constants (must match mapping_dpr.csv exactly)
M_PROD = 'Crude oil production'
M_RIGS = 'Active rigs'
M_DRILLED = 'New wells drilled'
M_COMPLETED = 'New wells completed'
M_DUCS = 'Cumulative drilled but uncompleted wells'
M_NEW_WELL = 'Crude oil production from newly completed wells, one-year trend'
M_NEW_WELL_RIG = 'Crude oil production from newly completed wells per rig, one-year trend'
M_LEGACY = 'Existing crude oil production change, one-year trend'
M_GAS_PROD = 'natural gas production'

COL_MAP = {
    M_PROD: 'production', M_RIGS: 'rigs', M_DRILLED: 'drilled',
    M_COMPLETED: 'completed', M_DUCS: 'ducs', M_NEW_WELL: 'new_well_prod',
    M_NEW_WELL_RIG: 'new_well_per_rig', M_LEGACY: 'legacy_decline',
    M_GAS_PROD: 'gas_production',
}


def _build_analysis_df():
    df = df_melted_dpr[
        (df_melted_dpr['release_date'] == LATEST_RELEASE) &
        (df_melted_dpr['region'].isin(REGIONS))
    ].copy()

    frames = []
    for region in REGIONS:
        rd = df[df['region'] == region]
        pivots = {}
        for metric_name, col_name in COL_MAP.items():
            s = rd[rd['name'] == metric_name][['delivery_month', 'value']]
            if not s.empty:
                s = s.drop_duplicates('delivery_month').set_index('delivery_month')
                pivots[col_name] = s['value']
        if pivots:
            rdf = pd.DataFrame(pivots)
            rdf['region'] = region
            frames.append(rdf)

    if not frames:
        return pd.DataFrame()
    result = pd.concat(frames).reset_index().rename(columns={'index': 'delivery_month'})
    return result.sort_values(['region', 'delivery_month']).reset_index(drop=True)


df_analysis = _build_analysis_df()

# ── Constants & Styling ──────────────────────────────────────────────────────

PAGE_STYLE = {"padding": "1.5rem 2rem", "backgroundColor": GRAY_50, "minHeight": "100vh"}
CHART_HEIGHT = 480
BASE_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    hovermode="x unified", height=CHART_HEIGHT,
    margin=dict(l=60, r=30, t=50, b=50),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    font=dict(family="Montserrat"),
    xaxis=dict(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300),
    yaxis=dict(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300),
)

LABEL_STYLE = {
    'fontSize': '0.72rem', 'fontWeight': '700', 'letterSpacing': '0.06em',
    'textTransform': 'uppercase', 'color': GRAY_500, 'marginBottom': '0.3rem',
}

KPI_CARD_STYLE = {
    'borderRadius': '6px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
    'backgroundColor': 'white', 'textAlign': 'center',
}

PERIOD_OPTIONS = [
    {'label': 'All Data', 'value': 'all'},
    {'label': 'Last 5 Years', 'value': '5y'},
    {'label': 'Last 3 Years', 'value': '3y'},
    {'label': 'Last 2 Years', 'value': '2y'},
    {'label': 'Last Year', 'value': '1y'},
]

PREDICTOR_OPTIONS = [
    {'label': 'Active Rigs', 'value': 'rigs'},
    {'label': 'Wells Completed', 'value': 'completed'},
    {'label': 'Wells Drilled', 'value': 'drilled'},
    {'label': 'DUC Inventory', 'value': 'ducs'},
    {'label': 'New-Well Prod/Rig', 'value': 'new_well_per_rig'},
]
PREDICTOR_LABELS = {p['value']: p['label'] for p in PREDICTOR_OPTIONS}


# ── Filtering Helpers ────────────────────────────────────────────────────────

def _filter_period(df, period):
    if period == 'all':
        return df
    years = {'1y': 1, '2y': 2, '3y': 3, '5y': 5}
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=years.get(period, 3))
    return df[df['delivery_month'] >= cutoff]


def _filter_forecast(df, include_forecast):
    if include_forecast:
        return df
    return df[df['delivery_month'] <= pd.Timestamp.now()]


# ── Tab 1: Rig Efficiency ───────────────────────────────────────────────────

def _make_efficiency_scatter(df):
    fig = go.Figure()
    stats_rows = []

    for region in REGIONS:
        rd = df[df['region'] == region].dropna(subset=['rigs', 'production'])
        if len(rd) < 3:
            continue

        color = REGION_COLORS[region]
        fig.add_trace(go.Scatter(
            x=rd['rigs'], y=rd['production'], mode='markers',
            name=region, marker=dict(color=color, size=8, opacity=0.7),
            hovertemplate=f'<b>{region}</b><br>Rigs: %{{x:.0f}}<br>Prod: %{{y:.2f}} mbd<extra></extra>',
        ))

        try:
            X = sm.add_constant(rd['rigs'].values)
            model = sm.OLS(rd['production'].values, X).fit()
            x_range = np.linspace(rd['rigs'].min(), rd['rigs'].max(), 50)
            y_pred = model.predict(sm.add_constant(x_range))
            fig.add_trace(go.Scatter(
                x=x_range, y=y_pred, mode='lines',
                line=dict(color=color, width=2, dash='dash'), showlegend=False,
                hovertemplate=f'<b>{region} OLS</b><br>R\u00b2={model.rsquared:.3f}<extra></extra>',
            ))
            stats_rows.append({
                'region': region, 'r2': model.rsquared,
                'slope': model.params[1], 'intercept': model.params[0],
                'p_value': model.pvalues[1], 'n': len(rd),
            })
        except Exception:
            pass

    layout_opts = {**BASE_LAYOUT, 'hovermode': 'closest'}
    fig.update_layout(
        **layout_opts,
        title=dict(text="Rig Count vs Oil Production by Basin", font=dict(size=14)),
        xaxis_title="Active Rigs (count)", yaxis_title="Crude Oil Production (mbd)",
    )
    return fig, pd.DataFrame(stats_rows)


def _make_productivity_trend(df):
    fig = go.Figure()
    for region in REGIONS:
        rd = df[df['region'] == region].dropna(subset=['new_well_per_rig']).sort_values('delivery_month')
        if rd.empty:
            continue
        fig.add_trace(go.Scatter(
            x=rd['delivery_month'], y=rd['new_well_per_rig'], mode='lines+markers',
            name=region, line=dict(color=REGION_COLORS[region], width=2.5), marker=dict(size=4),
        ))

    fig.update_layout(
        **{**BASE_LAYOUT, 'height': 380},
        title=dict(text="New-Well Oil Production per Rig (Technology Curve)", font=dict(size=14)),
        xaxis_title="", yaxis_title="kbd per rig",
    )
    return fig


# ── Tab 2: Drilling Treadmill ────────────────────────────────────────────────

def _make_treadmill_chart(df, region):
    rd = df[df['region'] == region].sort_values('delivery_month').dropna(subset=['new_well_prod', 'legacy_decline'])
    if rd.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=rd['delivery_month'], y=rd['new_well_prod'],
        name='New-Well Production', marker_color=GREEN, opacity=0.8,
    ), secondary_y=False)

    fig.add_trace(go.Bar(
        x=rd['delivery_month'], y=rd['legacy_decline'],
        name='Legacy Decline', marker_color=RED, opacity=0.8,
    ), secondary_y=False)

    prod = rd.dropna(subset=['production'])
    if not prod.empty:
        fig.add_trace(go.Scatter(
            x=prod['delivery_month'], y=prod['production'],
            name='Total Production', mode='lines+markers',
            line=dict(color=BLACK, width=3), marker=dict(size=5),
        ), secondary_y=True)

    fig.update_layout(
        barmode='relative',
        plot_bgcolor="white", paper_bgcolor="white",
        height=CHART_HEIGHT, margin=dict(l=60, r=60, t=50, b=50),
        font=dict(family="Montserrat"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        title=dict(text=f"{region} \u2014 Drilling Treadmill Analysis", font=dict(size=14)),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRAY_200, showline=True, linecolor=GRAY_300)
    fig.update_yaxes(title_text="Change (kbd)", secondary_y=False, showgrid=True, gridcolor=GRAY_200)
    fig.update_yaxes(title_text="Total Production (mbd)", secondary_y=True)
    return fig


def _make_duc_chart(df, region):
    rd = df[df['region'] == region].sort_values('delivery_month').dropna(subset=['ducs'])
    if rd.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rd['delivery_month'], y=rd['ducs'], mode='lines+markers',
        fill='tozeroy', line=dict(color=ORANGE, width=2.5),
        fillcolor='rgba(246,142,47,0.1)', name='DUC Inventory',
    ))
    fig.update_layout(
        **{**BASE_LAYOUT, 'height': 320},
        title=dict(text=f"{region} \u2014 DUC Well Inventory", font=dict(size=13)),
        xaxis_title="", yaxis_title="Wells (count)",
    )
    return fig


def _make_completion_rate_chart(df, region):
    rd = df[df['region'] == region].sort_values('delivery_month').dropna(subset=['completed', 'drilled'])
    rd = rd[rd['drilled'] > 0].copy()
    if rd.empty:
        return go.Figure()

    rd['completion_rate'] = rd['completed'] / rd['drilled']

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rd['delivery_month'], y=rd['completion_rate'],
        marker_color=[GREEN if r >= 1 else RED for r in rd['completion_rate']],
        name='Completion Rate',
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color=BLACK, line_width=1.5,
                  annotation_text="100%", annotation_position="right")

    fig.update_layout(
        **{**BASE_LAYOUT, 'height': 320},
        title=dict(text=f"{region} \u2014 Completion Rate (Completed / Drilled)", font=dict(size=13)),
        xaxis_title="", yaxis_title="Ratio",
    )
    return fig


def _compute_treadmill_kpis(df, region):
    rd = df[df['region'] == region].sort_values('delivery_month').dropna(subset=['new_well_prod', 'legacy_decline'])
    if rd.empty:
        return {}

    latest = rd.iloc[-1]
    nw = latest.get('new_well_prod', 0)
    ld = latest.get('legacy_decline', 0)
    prod = latest.get('production', 0)
    rigs = latest.get('rigs', 0)

    ratio = abs(nw / ld) if ld != 0 else float('inf')
    decline_pct = (ld / (prod * 1000)) * 100 if prod > 0 else 0

    return {
        'production': f'{prod:.2f} mbd',
        'new_well': f'{nw:.1f} kbd',
        'legacy': f'{ld:.1f} kbd',
        'ratio': f'{ratio:.2f}',
        'decline_pct': f'{decline_pct:.1f}%',
        'rigs': f'{rigs:.0f}',
        'month': latest['delivery_month'].strftime('%b %Y'),
    }


# ── Tab 3: Cross-Basin Correlations ──────────────────────────────────────────

def _make_correlation_heatmap(df, metric_col):
    pivot = df.pivot_table(index='delivery_month', columns='region', values=metric_col)
    pivot = pivot[[r for r in REGIONS if r in pivot.columns]]
    corr = pivot.corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
        text=[[f'{v:.2f}' for v in row] for row in corr.values],
        texttemplate='%{text}', textfont=dict(size=12, family='Montserrat'),
        colorscale=COLORSCALE_EFFICIENCY, zmid=0, zmin=-1, zmax=1,
        xgap=3, ygap=3,
        colorbar=dict(title='Correlation', thickness=14, len=0.85),
    ))

    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        height=450, margin=dict(l=130, r=40, t=50, b=100),
        font=dict(family="Montserrat"),
        title=dict(text="Cross-Basin Correlation Matrix", font=dict(size=14)),
        xaxis=dict(tickangle=-45),
    )
    return fig


def _make_rolling_correlation(df, metric_col, r1, r2, window=12):
    pivot = df.pivot_table(index='delivery_month', columns='region', values=metric_col)
    if r1 not in pivot.columns or r2 not in pivot.columns:
        return go.Figure()

    rolling_corr = pivot[r1].rolling(window).corr(pivot[r2])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rolling_corr.index, y=rolling_corr.values,
        mode='lines', line=dict(color=BLUE, width=2.5),
        fill='tozeroy', fillcolor='rgba(0,173,239,0.1)',
        name=f'{r1} vs {r2}',
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=GRAY_300)

    fig.update_layout(
        **{**BASE_LAYOUT, 'height': 350},
        title=dict(text=f"Rolling {window}-Month Correlation: {r1} vs {r2}", font=dict(size=13)),
        xaxis_title="", yaxis_title="Correlation",
        yaxis=dict(range=[-1.05, 1.05], showgrid=True, gridcolor=GRAY_200),
    )
    return fig


def _make_pair_scatter(df, metric_col, r1, r2):
    pivot = df.pivot_table(index='delivery_month', columns='region', values=metric_col).dropna(subset=[r1, r2])
    if pivot.empty or len(pivot) < 3:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pivot[r1], y=pivot[r2], mode='markers',
        marker=dict(color=BLUE, size=8, opacity=0.6), name='Observations',
    ))

    x, y = pivot[r1].values, pivot[r2].values
    slope, intercept, r_value, _, _ = scipy_stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 50)
    fig.add_trace(go.Scatter(
        x=x_line, y=intercept + slope * x_line,
        mode='lines', line=dict(color=RED, width=2, dash='dash'),
        name=f'R\u00b2={r_value**2:.3f}',
    ))

    layout_opts = {**BASE_LAYOUT, 'hovermode': 'closest', 'height': 380}
    fig.update_layout(
        **layout_opts,
        title=dict(text=f"{r1} vs {r2}", font=dict(size=13)),
        xaxis_title=r1, yaxis_title=r2,
    )
    return fig


# ── Tab 4: Regression Lab ───────────────────────────────────────────────────

def _run_regression(df, region, predictors, dep_var='production'):
    rd = df[df['region'] == region].dropna(subset=[dep_var] + predictors).sort_values('delivery_month')
    if len(rd) < len(predictors) + 2:
        return None, None, None, {}

    X = rd[predictors].values
    y = rd[dep_var].values
    dates = rd['delivery_month'].values

    try:
        model = sm.OLS(y, sm.add_constant(X)).fit()
    except Exception:
        return None, None, None, {}

    y_pred = model.predict(sm.add_constant(X))
    residuals = model.resid

    # Coefficient chart with CI whiskers
    params = model.params[1:]
    conf = model.conf_int().iloc[1:]
    pvals = model.pvalues[1:]
    labels = [PREDICTOR_LABELS.get(p, p) for p in predictors]
    colors = [GREEN if pv < 0.05 else ORANGE if pv < 0.1 else RED for pv in pvals]

    coef_fig = go.Figure()
    coef_fig.add_trace(go.Bar(
        x=labels, y=params,
        error_y=dict(
            type='data', symmetric=False,
            array=conf.iloc[:, 1].values - params,
            arrayminus=params - conf.iloc[:, 0].values,
        ),
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>Coef: %{y:.4f}<br>p-value: %{customdata:.4f}<extra></extra>',
        customdata=pvals,
    ))
    coef_fig.update_layout(
        **{**BASE_LAYOUT, 'height': 350},
        title=dict(text="Regression Coefficients (95% CI)", font=dict(size=13)),
        xaxis_title="", yaxis_title="Coefficient", showlegend=False,
    )
    coef_fig.add_annotation(
        text="Green: p<0.05 | Orange: p<0.10 | Red: p\u22650.10",
        xref="paper", yref="paper", x=1, y=-0.18,
        showarrow=False, font=dict(size=10, color=GRAY_500),
    )

    # Actual vs Predicted
    pred_fig = go.Figure()
    pred_fig.add_trace(go.Scatter(
        x=y, y=y_pred, mode='markers',
        marker=dict(color=BLUE, size=7, opacity=0.7), name='Observations',
    ))
    mn, mx = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
    pred_fig.add_trace(go.Scatter(
        x=[mn, mx], y=[mn, mx], mode='lines',
        line=dict(color=GRAY_300, width=2, dash='dash'), showlegend=False,
    ))
    layout_opts = {**BASE_LAYOUT, 'hovermode': 'closest', 'height': 380}
    pred_fig.update_layout(
        **layout_opts,
        title=dict(text=f"Actual vs Predicted (R\u00b2={model.rsquared:.4f})", font=dict(size=13)),
        xaxis_title="Actual (mbd)", yaxis_title="Predicted (mbd)",
    )

    # Residuals over time
    resid_fig = go.Figure()
    resid_fig.add_trace(go.Scatter(
        x=dates, y=residuals, mode='lines+markers',
        line=dict(color=BLUE, width=1.5), marker=dict(size=5), name='Residuals',
    ))
    resid_fig.add_hline(y=0, line_dash="dash", line_color=GRAY_300, line_width=1.5)
    sigma = residuals.std()
    resid_fig.add_hline(y=2 * sigma, line_dash="dot", line_color=RED, opacity=0.5,
                        annotation_text="+2\u03c3", annotation_position="right")
    resid_fig.add_hline(y=-2 * sigma, line_dash="dot", line_color=RED, opacity=0.5,
                        annotation_text="-2\u03c3", annotation_position="right")
    resid_fig.update_layout(
        **{**BASE_LAYOUT, 'height': 320},
        title=dict(text="Residuals Over Time", font=dict(size=13)),
        xaxis_title="", yaxis_title="Residual (mbd)",
    )

    try:
        dw = sm.stats.stattools.durbin_watson(residuals)
        dw_str = f'{dw:.3f}'
    except Exception:
        dw_str = 'N/A'

    summary = {
        'r2': f'{model.rsquared:.4f}',
        'adj_r2': f'{model.rsquared_adj:.4f}',
        'f_stat': f'{model.fvalue:.2f}',
        'f_pvalue': f'{model.f_pvalue:.4f}',
        'aic': f'{model.aic:.1f}',
        'bic': f'{model.bic:.1f}',
        'dw': dw_str,
        'n_obs': str(int(model.nobs)),
    }

    return coef_fig, pred_fig, resid_fig, summary


# ── Layout ───────────────────────────────────────────────────────────────────

REGION_DROPDOWN = [{'label': r, 'value': r} for r in REGIONS]

layout = html.Div([
    # Hero Header
    html.Div([
        html.Div([
            html.H1("DPR Basin Analytics Lab",
                     style={"fontSize": "2rem", "fontWeight": "700", "color": BLUE, "margin": "0"}),
            html.P(f"Release: {LATEST_RELEASE.strftime('%B %Y')} \u00b7 Statistical Analysis across {len(REGIONS)} Major Basins",
                   style={"fontSize": "0.85rem", "color": GRAY_500, "margin": "0"}),
        ]),
    ], className="dpr-hero"),

    # Tabs
    dbc.Tabs(id="analytics-tabs", active_tab="tab-efficiency", children=[
        dbc.Tab(label="Rig Efficiency", tab_id="tab-efficiency"),
        dbc.Tab(label="Drilling Treadmill", tab_id="tab-treadmill"),
        dbc.Tab(label="Basin Correlations", tab_id="tab-correlations"),
        dbc.Tab(label="Regression Lab", tab_id="tab-regression"),
    ]),

    html.Div(id="analytics-tab-content", children=[
        # ── Tab 1: Rig Efficiency ────────────────────────────────────────────
        html.Div(id="analytics-efficiency", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Time Period", style=LABEL_STYLE),
                    dcc.Dropdown(id="eff-period", options=PERIOD_OPTIONS,
                                 value='all', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=3, md=4),
                dbc.Col([
                    html.Label("Include Forecasts", style=LABEL_STYLE),
                    dbc.Switch(id="eff-forecast", value=False, label="Show forecast periods"),
                ], lg=3, md=4),
            ], className="g-3 align-items-end", style={"marginBottom": "1rem"}),

            html.Div(id="eff-stats-strip", style={"marginBottom": "1rem"}),

            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="eff-scatter", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=7),
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="eff-trend", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=5),
            ], className="g-3"),
        ]),

        # ── Tab 2: Drilling Treadmill ────────────────────────────────────────
        html.Div(id="analytics-treadmill", style={"display": "none"}, children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Region", style=LABEL_STYLE),
                    dcc.Dropdown(id="tread-region", options=REGION_DROPDOWN,
                                 value='Permian', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=3, md=4),
                dbc.Col([
                    html.Label("Time Period", style=LABEL_STYLE),
                    dcc.Dropdown(id="tread-period", options=PERIOD_OPTIONS,
                                 value='3y', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=3, md=4),
            ], className="g-3 align-items-end", style={"marginBottom": "1rem"}),

            html.Div(id="tread-kpi-strip", style={"marginBottom": "1rem"}),

            dbc.Card(dbc.CardBody(
                dcc.Graph(id="tread-chart", config={"displayModeBar": False})
            ), className="surface-card"),

            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="tread-duc", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=6),
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="tread-completion", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=6),
            ], className="g-3", style={"marginTop": "1rem"}),
        ]),

        # ── Tab 3: Basin Correlations ────────────────────────────────────────
        html.Div(id="analytics-correlations", style={"display": "none"}, children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Metric", style=LABEL_STYLE),
                    dcc.Dropdown(id="corr-metric", options=[
                        {'label': 'Oil Production', 'value': 'production'},
                        {'label': 'Gas Production', 'value': 'gas_production'},
                        {'label': 'Active Rigs', 'value': 'rigs'},
                        {'label': 'Wells Completed', 'value': 'completed'},
                        {'label': 'New-Well Prod/Rig', 'value': 'new_well_per_rig'},
                    ], value='production', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=3, md=4),
                dbc.Col([
                    html.Label("Basin Pair", style=LABEL_STYLE),
                    dcc.Dropdown(id="corr-r1", options=REGION_DROPDOWN,
                                 value='Permian', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=2, md=3),
                dbc.Col([
                    html.Label("\u00a0", style=LABEL_STYLE),
                    dcc.Dropdown(id="corr-r2", options=REGION_DROPDOWN,
                                 value='Eagle Ford', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=2, md=3),
                dbc.Col([
                    html.Label("Rolling Window", style=LABEL_STYLE),
                    dbc.RadioItems(id="corr-window", options=[
                        {'label': '6m', 'value': 6},
                        {'label': '12m', 'value': 12},
                        {'label': '24m', 'value': 24},
                    ], value=12, inline=True),
                ], lg=3, md=4),
            ], className="g-3 align-items-end", style={"marginBottom": "1rem"}),

            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="corr-heatmap", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=5),
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="corr-pair-scatter", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=7),
            ], className="g-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="corr-rolling", config={"displayModeBar": False})
                    ), className="surface-card"),
                ]),
            ], className="g-3", style={"marginTop": "1rem"}),
        ]),

        # ── Tab 4: Regression Lab ────────────────────────────────────────────
        html.Div(id="analytics-regression", style={"display": "none"}, children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Region", style=LABEL_STYLE),
                    dcc.Dropdown(id="reg-region", options=REGION_DROPDOWN,
                                 value='Permian', clearable=False, style={"fontSize": "0.85rem"}),
                ], lg=2, md=3),
                dbc.Col([
                    html.Label("Predictors", style=LABEL_STYLE),
                    dcc.Checklist(id="reg-predictors", options=PREDICTOR_OPTIONS,
                                  value=['rigs', 'completed', 'ducs'],
                                  inline=True, style={"fontSize": "0.82rem"},
                                  inputStyle={"marginRight": "4px"},
                                  labelStyle={"marginRight": "12px"}),
                ], lg=7, md=6),
                dbc.Col([
                    html.Label("Include Forecasts", style=LABEL_STYLE),
                    dbc.Switch(id="reg-forecast", value=False, label="Forecasts"),
                ], lg=2, md=3),
            ], className="g-3 align-items-end", style={"marginBottom": "1rem"}),

            html.Div(id="reg-summary-strip", style={"marginBottom": "1rem"}),

            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="reg-coefficients", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=5),
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="reg-actual-pred", config={"displayModeBar": False})
                    ), className="surface-card"),
                ], lg=7),
            ], className="g-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Card(dbc.CardBody(
                        dcc.Graph(id="reg-residuals", config={"displayModeBar": False})
                    ), className="surface-card"),
                ]),
            ], className="g-3", style={"marginTop": "1rem"}),
        ]),
    ]),
], style=PAGE_STYLE)


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

# 1. Tab switching
@callback(
    [Output("analytics-efficiency", "style"),
     Output("analytics-treadmill", "style"),
     Output("analytics-correlations", "style"),
     Output("analytics-regression", "style")],
    Input("analytics-tabs", "active_tab"),
)
def switch_analytics_tab(active_tab):
    show = {"display": "block"}
    hide = {"display": "none"}
    return (
        show if active_tab == "tab-efficiency" else hide,
        show if active_tab == "tab-treadmill" else hide,
        show if active_tab == "tab-correlations" else hide,
        show if active_tab == "tab-regression" else hide,
    )


# 2. Rig Efficiency
@callback(
    [Output("eff-scatter", "figure"),
     Output("eff-trend", "figure"),
     Output("eff-stats-strip", "children")],
    [Input("eff-period", "value"),
     Input("eff-forecast", "value")],
)
def update_efficiency(period, include_forecast):
    df = _filter_forecast(_filter_period(df_analysis, period), include_forecast)

    scatter_fig, stats_df = _make_efficiency_scatter(df)
    trend_fig = _make_productivity_trend(df)

    cards = []
    if not stats_df.empty:
        stats_df = stats_df.sort_values('slope', ascending=False)
        for _, row in stats_df.iterrows():
            color = REGION_COLORS.get(row['region'], GRAY_500)
            card = dbc.Card(dbc.CardBody([
                html.Div(row['region'], style={**LABEL_STYLE, 'marginBottom': '0.2rem'}),
                html.Div(f"{row['slope']:.4f}", style={
                    'fontSize': '1.2rem', 'fontWeight': '700', 'color': GRAY_800, 'lineHeight': '1',
                }),
                html.Div(f"mbd/rig \u00b7 R\u00b2={row['r2']:.3f}", style={
                    'fontSize': '0.72rem', 'color': GRAY_500, 'marginTop': '2px',
                }),
            ], style={'padding': '0.6rem 0.8rem'}), style={
                'borderLeft': f'3px solid {color}', **KPI_CARD_STYLE,
            })
            cards.append(dbc.Col(card, lg=2, md=4, sm=6))

    strip = dbc.Row(cards, className='g-3') if cards else html.Div()
    return scatter_fig, trend_fig, strip


# 3. Drilling Treadmill
@callback(
    [Output("tread-chart", "figure"),
     Output("tread-duc", "figure"),
     Output("tread-completion", "figure"),
     Output("tread-kpi-strip", "children")],
    [Input("tread-region", "value"),
     Input("tread-period", "value")],
)
def update_treadmill(region, period):
    df = _filter_period(df_analysis, period)
    tread_fig = _make_treadmill_chart(df, region)
    duc_fig = _make_duc_chart(df, region)
    comp_fig = _make_completion_rate_chart(df, region)
    kpis = _compute_treadmill_kpis(df, region)

    if not kpis:
        return tread_fig, duc_fig, comp_fig, html.Div()

    color = REGION_COLORS.get(region, BLUE)
    items = [
        ('Production', kpis['production'], 'Latest total'),
        ('New-Well Add', kpis['new_well'], 'Monthly contribution'),
        ('Legacy Decline', kpis['legacy'], 'Monthly erosion'),
        ('Treadmill Ratio', kpis['ratio'] + 'x', 'New / |Decline|'),
        ('Decline Rate', kpis['decline_pct'], '% of total/month'),
        ('Active Rigs', kpis['rigs'], f"As of {kpis['month']}"),
    ]

    cards = []
    for title, value, subtitle in items:
        is_ratio = title == 'Treadmill Ratio'
        try:
            val_color = POSITIVE if is_ratio and float(kpis['ratio']) > 1 else (NEGATIVE if is_ratio else GRAY_800)
        except (ValueError, KeyError):
            val_color = GRAY_800

        card = dbc.Card(dbc.CardBody([
            html.Div(title, style={**LABEL_STYLE, 'marginBottom': '0.15rem'}),
            html.Div(value, style={
                'fontSize': '1.2rem', 'fontWeight': '700', 'color': val_color, 'lineHeight': '1',
            }),
            html.Div(subtitle, style={'fontSize': '0.68rem', 'color': GRAY_500, 'marginTop': '2px'}),
        ], style={'padding': '0.6rem 0.8rem'}), style={
            'borderLeft': f'3px solid {color}', **KPI_CARD_STYLE,
        })
        cards.append(dbc.Col(card, lg=2, md=4, sm=6))

    return tread_fig, duc_fig, comp_fig, dbc.Row(cards, className='g-3')


# 4. Cross-Basin Correlations
@callback(
    [Output("corr-heatmap", "figure"),
     Output("corr-pair-scatter", "figure"),
     Output("corr-rolling", "figure")],
    [Input("corr-metric", "value"),
     Input("corr-r1", "value"),
     Input("corr-r2", "value"),
     Input("corr-window", "value")],
)
def update_correlations(metric, r1, r2, window):
    heatmap = _make_correlation_heatmap(df_analysis, metric)
    scatter = _make_pair_scatter(df_analysis, metric, r1, r2)
    rolling = _make_rolling_correlation(df_analysis, metric, r1, r2, window)
    return heatmap, scatter, rolling


# 5. Regression Lab
@callback(
    [Output("reg-coefficients", "figure"),
     Output("reg-actual-pred", "figure"),
     Output("reg-residuals", "figure"),
     Output("reg-summary-strip", "children")],
    [Input("reg-region", "value"),
     Input("reg-predictors", "value"),
     Input("reg-forecast", "value")],
)
def update_regression(region, predictors, include_forecast):
    empty = go.Figure()
    empty.update_layout(**{**BASE_LAYOUT, 'height': 350})

    if not predictors:
        msg = html.Div("Select at least one predictor",
                        style={"color": GRAY_500, "textAlign": "center", "padding": "2rem"})
        return empty, empty, empty, msg

    df = _filter_forecast(df_analysis, include_forecast)
    coef_fig, pred_fig, resid_fig, summary = _run_regression(df, region, predictors)

    if coef_fig is None:
        msg = html.Div("Insufficient data for regression",
                        style={"color": GRAY_500, "textAlign": "center", "padding": "2rem"})
        return empty, empty, empty, msg

    color = REGION_COLORS.get(region, BLUE)
    stat_items = [
        ('R\u00b2', summary['r2']),
        ('Adj R\u00b2', summary['adj_r2']),
        ('F-Statistic', summary['f_stat']),
        ('F p-value', summary['f_pvalue']),
        ('AIC', summary['aic']),
        ('BIC', summary['bic']),
        ('Durbin-Watson', summary['dw']),
        ('Observations', summary['n_obs']),
    ]

    cards = []
    for title, value in stat_items:
        card = dbc.Card(dbc.CardBody([
            html.Div(title, style={**LABEL_STYLE, 'marginBottom': '0.1rem', 'fontSize': '0.65rem'}),
            html.Div(value, style={
                'fontSize': '1rem', 'fontWeight': '700', 'color': GRAY_800,
                'lineHeight': '1', 'fontFeatureSettings': "'tnum'",
            }),
        ], style={'padding': '0.5rem 0.6rem'}), style={
            'borderTop': f'3px solid {color}', **KPI_CARD_STYLE,
        })
        cards.append(dbc.Col(card))

    strip = dbc.Row(cards, className='g-2')
    return coef_fig, pred_fig, resid_fig, strip
