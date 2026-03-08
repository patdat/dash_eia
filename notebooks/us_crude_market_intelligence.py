# %% [markdown]
# # US Crude Oil Market Intelligence Report
#
# A cross-dataset analysis combining EIA Weekly Petroleum Status (WPS),
# Company-Level Imports (CLI), and Drilling Productivity Report (DPR) data
# to build a comprehensive picture of the US crude oil market.

# %%
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

import sys, os
import plotly.io as pio

# Set plotly renderer for VS Code interactive window
try:
    get_ipython()  # only exists in IPython/Jupyter
    pio.renderers.default = 'notebook'
except NameError:
    pass  # plain python — fig.show() opens browser, which is fine

# Resolve project root — works as `python script.py`, in VS Code #%% cells, and Jupyter
try:
    _this_file = os.path.abspath(__file__)
    _this_dir = os.path.dirname(_this_file)
except NameError:
    _this_dir = os.getcwd()

ROOT = os.path.abspath(os.path.join(_this_dir, '..')) if os.path.basename(_this_dir) == 'notebooks' else _this_dir

# Ensure we can find data/ and src/
if not os.path.isdir(os.path.join(ROOT, 'data')):
    # Fallback: walk up until we find the project root
    _search = os.getcwd()
    for _ in range(5):
        if os.path.isdir(os.path.join(_search, 'data')):
            ROOT = _search
            break
        _search = os.path.dirname(_search)

os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# %%
# Load all datasets
wps_pivot = pd.read_feather(os.path.join(ROOT, 'data/wps/wps_gte_2015_pivot.feather'))
wps_long = pd.read_feather(os.path.join(ROOT, 'data/wps/wps_gte_2015.feather'))
seasonality = pd.read_feather(os.path.join(ROOT, 'data/wps/seasonality_data.feather'))
cli_crude = pd.read_parquet(os.path.join(ROOT, 'data/cli/companylevelimports_crude.parquet'))
steo_dpr = pd.read_feather(os.path.join(ROOT, 'data/steo/steo_pivot_dpr.feather'))
steo_dpr_other = pd.read_feather(os.path.join(ROOT, 'data/steo/steo_pivot_dpr_other.feather'))

# Load mappings
from src.wps.mapping import production_mapping
dpr_mapping = pd.read_csv(os.path.join(ROOT, 'lookup/steo/mapping_dpr.csv'))

print(f"WPS Pivot:      {wps_pivot.shape[0]} weeks  ({wps_pivot['period'].min().date()} → {wps_pivot['period'].max().date()})")
cli_crude['RPT_PERIOD'] = pd.to_datetime(cli_crude['RPT_PERIOD'])
print(f"CLI Crude:      {cli_crude.shape[0]:,} records ({cli_crude['RPT_PERIOD'].min().strftime('%Y-%m')} → {cli_crude['RPT_PERIOD'].max().strftime('%Y-%m')})")
print(f"STEO DPR:       {steo_dpr.shape[0]} series")
print(f"DPR Mapping:    {dpr_mapping.shape[0]} series across {dpr_mapping['region'].nunique()} regions")

# %% [markdown]
# ---
# ## 1. The US Crude Balance Sheet — Weekly Pulse
#
# Let's build a comprehensive supply/demand balance from the weekly data,
# tracking production, imports, exports, refinery demand, and the resulting stock change.

# %%
# Key series for crude balance
balance_ids = {
    'WCRFPUS2': 'Production',
    'WCEIMUS2': 'Imports',
    'WCREXUS2': 'Exports',
    'WCRRIUS2': 'Refinery Runs',
    'WCESTUS1': 'Commercial Stocks',
    'WCSSTUS1': 'SPR Stocks',
}

balance = wps_pivot[['period'] + [k for k in balance_ids.keys() if k in wps_pivot.columns]].copy()
balance.columns = ['period'] + [balance_ids[c] for c in balance.columns if c != 'period']
balance = balance.set_index('period').sort_index()

# Calculate net balance (supply - demand proxy)
balance['Net Imports'] = balance['Imports'] - balance['Exports']
balance['Implied Demand'] = balance['Refinery Runs']  # crude runs as demand proxy
balance['Supply'] = balance['Production'] + balance['Net Imports']
balance['Balance'] = balance['Supply'] - balance['Implied Demand']

# 4-week moving averages for smoother view
balance_ma = balance.rolling(4).mean()

# %%
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
    subplot_titles=(
        'US Crude Supply Stack (4wk avg, kbd)',
        'Supply vs Demand (4wk avg, kbd)',
        'Commercial + SPR Stocks (kb)'
    ),
    row_heights=[0.35, 0.35, 0.30]
)

colors = {'Production': '#2563eb', 'Net Imports': '#f59e0b', 'Exports': '#ef4444'}

# Panel 1: Supply stack
fig.add_trace(go.Scatter(
    x=balance_ma.index, y=balance_ma['Production'],
    name='Production', fill='tozeroy',
    line=dict(color=colors['Production'], width=0),
    fillcolor='rgba(37, 99, 235, 0.4)'
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=balance_ma.index, y=balance_ma['Production'] + balance_ma['Net Imports'],
    name='+ Net Imports', fill='tonexty',
    line=dict(color=colors['Net Imports'], width=0),
    fillcolor='rgba(245, 158, 11, 0.4)'
), row=1, col=1)

# Panel 2: Supply vs Demand
fig.add_trace(go.Scatter(
    x=balance_ma.index, y=balance_ma['Supply'],
    name='Supply (Prod + Net Imp)', line=dict(color='#2563eb', width=2)
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=balance_ma.index, y=balance_ma['Implied Demand'],
    name='Refinery Demand', line=dict(color='#ef4444', width=2)
), row=2, col=1)

# Panel 3: Stocks
fig.add_trace(go.Scatter(
    x=balance.index, y=balance['Commercial Stocks'],
    name='Commercial', line=dict(color='#8b5cf6', width=2)
), row=3, col=1)
fig.add_trace(go.Scatter(
    x=balance.index, y=balance['SPR Stocks'],
    name='SPR', line=dict(color='#6b7280', width=2, dash='dash')
), row=3, col=1)
fig.add_trace(go.Scatter(
    x=balance.index, y=balance['Commercial Stocks'] + balance['SPR Stocks'],
    name='Total', line=dict(color='#1f2937', width=2.5)
), row=3, col=1)

fig.update_layout(
    height=900, template='plotly_white',
    title='US Crude Oil Balance Sheet — Weekly View',
    legend=dict(orientation='h', y=-0.05),
    hovermode='x unified'
)
fig.update_yaxes(title_text='kbd', row=1, col=1)
fig.update_yaxes(title_text='kbd', row=2, col=1)
fig.update_yaxes(title_text='kb (thousands)', row=3, col=1)
fig.show()

# %% [markdown]
# ---
# ## 2. Seasonality Heatmap — Every Product, Every Week
#
# Build a single heatmap showing how each major petroleum product deviates
# from its own seasonal norm in 2025 vs the 2021-2025 average.

# %%
# Pick headline series for each commodity
headline_ids = {
    'WCESTUS1': 'Crude Stocks',
    'WGTSTUS1': 'Gasoline Stocks',
    'WDISTUS1': 'Distillate Stocks',
    'WKJSTUS1': 'Jet Fuel Stocks',
    'WRESTUS1': 'Residual FO Stocks',
    'WPRSTUS1': 'Propane Stocks',
    'WCRFPUS2': 'Crude Production',
    'WGFRPUS2': 'Gasoline Production',
    'W_EPM0F_EEX_NUS-Z00_MBBLD': 'Gasoline Exports',
    'WCREXUS2': 'Crude Exports',
}

# Build deviation matrix: (2025 actual - avg_2125) / avg_2125 * 100
available_ids = [k for k in headline_ids if k in seasonality['id'].values]
seasonal_sub = seasonality[seasonality['id'].isin(available_ids)].copy()

# Check which average column exists
avg_col = 'average_2125' if 'average_2125' in seasonal_sub.columns else None
actual_col = 'actual_2025' if 'actual_2025' in seasonal_sub.columns else 'actual_2024'

if avg_col and actual_col:
    seasonal_sub['deviation_pct'] = (
        (seasonal_sub[actual_col] - seasonal_sub[avg_col]) / seasonal_sub[avg_col] * 100
    )

    pivot_heat = seasonal_sub.pivot_table(
        index='id', columns='week_of_year', values='deviation_pct'
    )
    # Rename index with friendly names
    pivot_heat.index = [headline_ids.get(i, i) for i in pivot_heat.index]

    # Only show weeks with data
    pivot_heat = pivot_heat.dropna(axis=1, how='all')

    fig = go.Figure(data=go.Heatmap(
        z=pivot_heat.values,
        x=[f'W{int(c)}' for c in pivot_heat.columns],
        y=pivot_heat.index,
        colorscale='RdBu_r',
        zmid=0,
        zmin=-15, zmax=15,
        colorbar=dict(title='% dev from<br>5yr avg'),
        hovertemplate='%{y}<br>Week %{x}<br>Deviation: %{z:.1f}%<extra></extra>'
    ))

    year_label = actual_col.replace('actual_', '')
    fig.update_layout(
        title=f'{year_label} Seasonal Deviation from 5-Year Average (2021-2025)',
        height=450, template='plotly_white',
        xaxis_title='Week of Year', yaxis_title='',
        yaxis=dict(autorange='reversed')
    )
    fig.show()
else:
    print("Seasonality columns not as expected — skipping heatmap")

# %% [markdown]
# ---
# ## 3. Where Does US Crude Come From? — Import Fingerprint
#
# Analyze the CLI data to build a picture of US crude sourcing:
# geographic concentration, quality mix, and how it's changed over time.

# %%
cli = cli_crude.copy()
cli['RPT_PERIOD'] = pd.to_datetime(cli['RPT_PERIOD'])
cli['DAYS_IN_MONTH'] = cli['RPT_PERIOD'].dt.daysinmonth
cli['KBD'] = cli['QUANTITY'] / cli['DAYS_IN_MONTH']
cli['YEAR'] = cli['RPT_PERIOD'].dt.year

# Top 10 source countries by total volume
top_countries = cli.groupby('CNTRY_NAME')['QUANTITY'].sum().nlargest(10).index.tolist()

# Monthly volume by country
monthly_country = (
    cli[cli['CNTRY_NAME'].isin(top_countries)]
    .groupby([pd.Grouper(key='RPT_PERIOD', freq='MS'), 'CNTRY_NAME'])['KBD']
    .sum()
    .reset_index()
)

fig = px.area(
    monthly_country, x='RPT_PERIOD', y='KBD', color='CNTRY_NAME',
    title='US Crude Imports by Source Country (kbd)',
    labels={'RPT_PERIOD': '', 'KBD': 'kbd', 'CNTRY_NAME': 'Country'},
    color_discrete_sequence=px.colors.qualitative.Set3,
    template='plotly_white'
)
fig.update_layout(height=500, legend=dict(orientation='h', y=-0.15))
fig.show()

# %%
# Country concentration — Herfindahl-Hirschman Index over time
yearly_country = cli.groupby(['YEAR', 'CNTRY_NAME'])['QUANTITY'].sum().reset_index()
yearly_total = yearly_country.groupby('YEAR')['QUANTITY'].transform('sum')
yearly_country['share'] = yearly_country['QUANTITY'] / yearly_total * 100

hhi_by_year = yearly_country.groupby('YEAR').apply(
    lambda g: (g['share'] ** 2).sum(), include_groups=False
).reset_index()
hhi_by_year.columns = ['Year', 'HHI']

fig = go.Figure()
fig.add_trace(go.Bar(
    x=hhi_by_year['Year'], y=hhi_by_year['HHI'],
    marker_color=np.where(hhi_by_year['HHI'] > 2500, '#ef4444',
                 np.where(hhi_by_year['HHI'] > 1500, '#f59e0b', '#22c55e')),
    text=hhi_by_year['HHI'].round(0).astype(int),
    textposition='outside'
))
fig.add_hline(y=2500, line_dash='dash', line_color='red',
              annotation_text='High Concentration', annotation_position='top left')
fig.add_hline(y=1500, line_dash='dash', line_color='orange',
              annotation_text='Moderate', annotation_position='top left')
fig.update_layout(
    title='Import Source Concentration (HHI by Country)',
    yaxis_title='Herfindahl-Hirschman Index',
    xaxis_title='', height=400, template='plotly_white',
    showlegend=False
)
fig.show()

# %% [markdown]
# ---
# ## 4. Crude Quality Landscape — API Gravity vs Sulfur Scatter
#
# Every import cargo plotted by its quality characteristics.
# Size = volume, color = source country. This reveals the quality
# "neighborhoods" that different suppliers occupy.

# %%
# Aggregate to country-month level for cleaner scatter
quality = (
    cli[cli['CNTRY_NAME'].isin(top_countries)]
    .groupby(['RPT_PERIOD', 'CNTRY_NAME'])
    .agg({'APIGRAVITY': 'mean', 'SULFUR': 'mean', 'QUANTITY': 'sum'})
    .reset_index()
)

fig = px.scatter(
    quality, x='APIGRAVITY', y='SULFUR', color='CNTRY_NAME',
    size='QUANTITY', size_max=18, opacity=0.6,
    title='Crude Import Quality Map — API Gravity vs Sulfur Content',
    labels={'APIGRAVITY': 'API Gravity (°)', 'SULFUR': 'Sulfur (%)',
            'CNTRY_NAME': 'Country', 'QUANTITY': 'Volume (mb)'},
    template='plotly_white',
    color_discrete_sequence=px.colors.qualitative.Set2
)

# Add quality quadrant labels
fig.add_vline(x=31, line_dash='dot', line_color='gray', opacity=0.5)
fig.add_hline(y=0.5, line_dash='dot', line_color='gray', opacity=0.5)
fig.add_annotation(x=40, y=0.15, text='Light Sweet', showarrow=False,
                   font=dict(size=11, color='green'))
fig.add_annotation(x=18, y=3.0, text='Heavy Sour', showarrow=False,
                   font=dict(size=11, color='red'))
fig.add_annotation(x=40, y=3.0, text='Light Sour', showarrow=False,
                   font=dict(size=11, color='orange'))
fig.add_annotation(x=18, y=0.15, text='Heavy Sweet', showarrow=False,
                   font=dict(size=11, color='blue'))

fig.update_layout(height=550, legend=dict(orientation='h', y=-0.15))
fig.show()

# %% [markdown]
# ---
# ## 5. Quality Mix Shift Over Time
#
# Has the US been importing lighter or heavier crude? Sweeter or more sour?
# Track the volume-weighted average quality by year.

# %%
# Volume-weighted quality by month
cli_monthly = cli.groupby('RPT_PERIOD').apply(
    lambda g: pd.Series({
        'wtd_api': np.average(g['APIGRAVITY'], weights=g['QUANTITY']),
        'wtd_sulfur': np.average(g['SULFUR'], weights=g['QUANTITY']),
        'total_kbd': g['KBD'].sum()
    }), include_groups=False
).reset_index()

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                    subplot_titles=('Volume-Weighted API Gravity (°)',
                                   'Volume-Weighted Sulfur Content (%)'))

# API with trend
fig.add_trace(go.Scatter(
    x=cli_monthly['RPT_PERIOD'], y=cli_monthly['wtd_api'],
    mode='markers', marker=dict(size=4, color='#6366f1', opacity=0.4),
    name='Monthly', showlegend=False
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=cli_monthly['RPT_PERIOD'], y=cli_monthly['wtd_api'].rolling(6).mean(),
    line=dict(color='#6366f1', width=3), name='API (6mo avg)'
), row=1, col=1)

# Sulfur with trend
fig.add_trace(go.Scatter(
    x=cli_monthly['RPT_PERIOD'], y=cli_monthly['wtd_sulfur'],
    mode='markers', marker=dict(size=4, color='#f97316', opacity=0.4),
    name='Monthly', showlegend=False
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=cli_monthly['RPT_PERIOD'], y=cli_monthly['wtd_sulfur'].rolling(6).mean(),
    line=dict(color='#f97316', width=3), name='Sulfur (6mo avg)'
), row=2, col=1)

fig.update_layout(
    height=550, template='plotly_white',
    title='Evolution of US Crude Import Quality',
    legend=dict(orientation='h', y=-0.08),
    hovermode='x unified'
)
fig.show()

# %% [markdown]
# ---
# ## 6. Refinery Appetite — PADD-Level Import Profiles
#
# Different PADDs import very different crudes. Let's profile each region.

# %%
padd_quality = (
    cli.groupby('PORT_PADD')
    .apply(lambda g: pd.Series({
        'Avg API': np.average(g['APIGRAVITY'], weights=g['QUANTITY']),
        'Avg Sulfur': np.average(g['SULFUR'], weights=g['QUANTITY']),
        'Total Volume (mb)': g['QUANTITY'].sum(),
        'Unique Countries': g['CNTRY_NAME'].nunique(),
        'Unique Companies': g['R_S_NAME'].nunique(),
        'Top Country': g.groupby('CNTRY_NAME')['QUANTITY'].sum().idxmax(),
        'Top Country %': g.groupby('CNTRY_NAME')['QUANTITY'].sum().max() / g['QUANTITY'].sum() * 100
    }), include_groups=False)
    .round(1)
)
padd_quality.index = [f'PADD {int(i)}' for i in padd_quality.index]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=('PADD Crude Quality Profile', 'PADD Import Volume & Diversity'),
    specs=[[{'type': 'scatter'}, {'type': 'bar'}]]
)

padd_colors = ['#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899']

for i, (padd, row) in enumerate(padd_quality.iterrows()):
    fig.add_trace(go.Scatter(
        x=[row['Avg API']], y=[row['Avg Sulfur']],
        mode='markers+text', text=[padd], textposition='top center',
        marker=dict(size=row['Total Volume (mb)'] / padd_quality['Total Volume (mb)'].max() * 50 + 10,
                    color=padd_colors[i], opacity=0.7),
        name=padd, showlegend=False
    ), row=1, col=1)

fig.add_trace(go.Bar(
    x=padd_quality.index, y=padd_quality['Unique Countries'],
    marker_color=padd_colors[:len(padd_quality)],
    name='Countries', showlegend=False
), row=1, col=2)

fig.update_xaxes(title_text='API Gravity (°)', row=1, col=1)
fig.update_yaxes(title_text='Sulfur (%)', row=1, col=1)
fig.update_yaxes(title_text='# Source Countries', row=1, col=2)

fig.update_layout(height=450, template='plotly_white',
                  title='PADD Import Profiles — Quality & Diversity')
fig.show()

print(padd_quality.to_string())

# %% [markdown]
# ---
# ## 7. Shale Revolution Tracker — DPR Production by Basin
#
# Use the STEO DPR data to track how US shale production has evolved
# across major basins, and where the latest forecasts point.

# %%
# Get crude oil production series from DPR mapping
prod_series = dpr_mapping[
    (dpr_mapping['name'].str.contains('Crude oil production', case=False)) &
    (~dpr_mapping['region'].isin(['US Total']))
].copy()

# Get the most recent release from steo_dpr
date_cols = [c for c in steo_dpr.columns if c not in ['id', 'name', 'release_date', 'uom']]
latest_release = steo_dpr['release_date'].max()
latest_dpr = steo_dpr[steo_dpr['release_date'] == latest_release].copy()

# Merge with mapping to get region names
dpr_prod = latest_dpr[latest_dpr['id'].isin(prod_series['id'].values)].copy()
dpr_prod = dpr_prod.merge(prod_series[['id', 'region']], on='id', how='left')

# Melt to long format
dpr_melted = dpr_prod.melt(
    id_vars=['id', 'name', 'region', 'release_date', 'uom'],
    var_name='period', value_name='production'
)
dpr_melted['period'] = pd.to_datetime(dpr_melted['period'])
dpr_melted = dpr_melted.dropna(subset=['production'])

fig = px.area(
    dpr_melted.sort_values(['period', 'production'], ascending=[True, False]),
    x='period', y='production', color='region',
    title=f'US Shale Crude Oil Production by Basin (Latest DPR: {latest_release})',
    labels={'period': '', 'production': 'Production (mbd)', 'region': 'Basin'},
    color_discrete_sequence=px.colors.qualitative.Bold,
    template='plotly_white'
)
fig.update_layout(height=500, legend=dict(orientation='h', y=-0.15))
fig.show()

# %% [markdown]
# ---
# ## 8. Forecast Evolution — How Has the Outlook Changed?
#
# Track how the Permian production forecast has been revised across
# successive STEO releases.

# %%
# Get Permian crude production series
permian_id = dpr_mapping[
    (dpr_mapping['region'] == 'Permian') &
    (dpr_mapping['name'].str.contains('Crude oil production', case=False))
]['id'].values

if len(permian_id) > 0:
    permian_id = permian_id[0]
    permian_forecasts = steo_dpr[steo_dpr['id'] == permian_id].copy()

    # Take last 6 releases for clarity
    releases = permian_forecasts['release_date'].sort_values().unique()
    recent_releases = releases[-6:] if len(releases) >= 6 else releases
    permian_recent = permian_forecasts[permian_forecasts['release_date'].isin(recent_releases)]

    fig = go.Figure()
    colors_evo = px.colors.sequential.Viridis

    for i, (_, row) in enumerate(permian_recent.iterrows()):
        vals = row[date_cols].dropna()
        periods = pd.to_datetime(vals.index)

        is_latest = (row['release_date'] == recent_releases[-1])
        fig.add_trace(go.Scatter(
            x=periods, y=vals.values.astype(float),
            name=str(row['release_date'])[:10],
            line=dict(
                width=3 if is_latest else 1.5,
                color=colors_evo[int(i * len(colors_evo) / len(recent_releases))]
            ),
            opacity=1.0 if is_latest else 0.6
        ))

    fig.update_layout(
        title='Permian Basin Crude Production — Forecast Evolution',
        yaxis_title='Production (mbd)',
        height=450, template='plotly_white',
        legend_title='Release Date',
        hovermode='x unified'
    )
    fig.show()
else:
    print("Permian production series not found in DPR mapping")

# %% [markdown]
# ---
# ## 9. Cross-Dataset: Import Quality vs Refinery Utilization
#
# Do refineries run harder when they're getting the crude quality they want?
# Merge weekly refinery utilization with monthly import quality data.

# %%
# Refinery utilization from WPS
util_id = 'WPULEUS3'  # US refinery utilization %
if util_id in wps_pivot.columns:
    util = wps_pivot[['period', util_id]].copy()
    util.columns = ['period', 'utilization']
    util['month'] = util['period'].dt.to_period('M')
    util_monthly = util.groupby('month')['utilization'].mean().reset_index()
    util_monthly['month'] = util_monthly['month'].dt.to_timestamp()

    # Merge with import quality
    merged = cli_monthly.merge(util_monthly, left_on='RPT_PERIOD', right_on='month', how='inner')

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=merged['month'], y=merged['utilization'],
        name='Refinery Utilization (%)',
        line=dict(color='#ef4444', width=2)
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=merged['month'], y=merged['wtd_api'],
        name='Import-Weighted API (°)',
        line=dict(color='#3b82f6', width=2)
    ), secondary_y=True)

    fig.update_layout(
        title='Refinery Utilization vs Import Crude Quality',
        height=400, template='plotly_white',
        legend=dict(orientation='h', y=-0.12),
        hovermode='x unified'
    )
    fig.update_yaxes(title_text='Utilization (%)', secondary_y=False)
    fig.update_yaxes(title_text='API Gravity (°)', secondary_y=True)
    fig.show()

    # Correlation
    r, p = stats.pearsonr(merged['utilization'].dropna(), merged['wtd_api'].dropna().iloc[:len(merged['utilization'].dropna())])
    print(f"Pearson correlation: r={r:.3f}, p={p:.4f}")
else:
    print(f"Utilization series {util_id} not found — checking available refinery series...")
    refinery_cols = [c for c in wps_pivot.columns if 'PUL' in c.upper() or 'util' in production_mapping.get(c, '').lower()]
    print(f"Found: {refinery_cols}")

# %% [markdown]
# ---
# ## 10. Importer Clustering — Who Sources Similarly?
#
# Use K-Means on importer profiles (API, Sulfur, country diversity, PADD mix)
# to find natural groupings among US crude importers.

# %%
# Build importer feature matrix
importer_features = (
    cli.groupby('R_S_NAME')
    .apply(lambda g: pd.Series({
        'avg_api': np.average(g['APIGRAVITY'], weights=g['QUANTITY']),
        'avg_sulfur': np.average(g['SULFUR'], weights=g['QUANTITY']),
        'country_count': g['CNTRY_NAME'].nunique(),
        'total_volume': g['QUANTITY'].sum(),
        'canada_pct': g[g['CNTRY_NAME'] == 'CANADA']['QUANTITY'].sum() / g['QUANTITY'].sum() * 100,
        'heavy_pct': g[g['APIGRAVITY'] < 22]['QUANTITY'].sum() / g['QUANTITY'].sum() * 100,
    }), include_groups=False)
)

# Filter to importers with meaningful volume (top 50)
top_importers = importer_features.nlargest(50, 'total_volume').copy()

# Standardize for clustering
features_for_clustering = ['avg_api', 'avg_sulfur', 'country_count', 'canada_pct', 'heavy_pct']
scaler = StandardScaler()
X = scaler.fit_transform(top_importers[features_for_clustering])

# K-Means with 4 clusters
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
top_importers['cluster'] = kmeans.fit_predict(X)

# PCA for visualization
pca = PCA(n_components=2)
coords = pca.fit_transform(X)
top_importers['pc1'] = coords[:, 0]
top_importers['pc2'] = coords[:, 1]

cluster_names = {0: 'Cluster A', 1: 'Cluster B', 2: 'Cluster C', 3: 'Cluster D'}
top_importers['cluster_name'] = top_importers['cluster'].map(cluster_names)

fig = px.scatter(
    top_importers.reset_index(), x='pc1', y='pc2',
    color='cluster_name', size='total_volume', size_max=30,
    hover_name='R_S_NAME',
    hover_data={'avg_api': ':.1f', 'avg_sulfur': ':.2f', 'canada_pct': ':.0f',
                'pc1': False, 'pc2': False, 'cluster_name': False},
    title='US Crude Importer Clusters (PCA Projection)',
    labels={'pc1': f'PC1 ({pca.explained_variance_ratio_[0]:.0%} var)',
            'pc2': f'PC2 ({pca.explained_variance_ratio_[1]:.0%} var)',
            'cluster_name': 'Cluster'},
    color_discrete_sequence=['#ef4444', '#3b82f6', '#22c55e', '#f59e0b'],
    template='plotly_white'
)
fig.update_layout(height=500)
fig.show()

# Cluster profiles
print("\n=== Cluster Profiles ===")
profiles = top_importers.groupby('cluster_name')[features_for_clustering + ['total_volume']].mean().round(1)
profiles['count'] = top_importers.groupby('cluster_name').size()
print(profiles.to_string())

# %% [markdown]
# ---
# ## 11. Production vs Stocks — Phase Space Diagram
#
# A creative visualization: plot production (x) vs stocks (y) as a trajectory
# through time. This reveals structural shifts in the production-inventory relationship.

# %%
phase = balance[['Production', 'Commercial Stocks']].dropna().copy()
phase['Production_ma'] = phase['Production'].rolling(13).mean()
phase['Stocks_ma'] = phase['Commercial Stocks'].rolling(13).mean()
phase = phase.dropna()

# Color by year
phase['year'] = phase.index.year

fig = go.Figure()

for year in sorted(phase['year'].unique()):
    yr_data = phase[phase['year'] == year]
    fig.add_trace(go.Scatter(
        x=yr_data['Production_ma'], y=yr_data['Stocks_ma'],
        mode='lines+markers',
        marker=dict(size=3),
        name=str(year),
        hovertemplate='%{text}<br>Prod: %{x:.0f} kbd<br>Stocks: %{y:,.0f} kb',
        text=[d.strftime('%b %d') for d in yr_data.index]
    ))

# Add arrows showing direction for latest year
latest_year = phase['year'].max()
ly = phase[phase['year'] == latest_year]
if len(ly) > 2:
    fig.add_annotation(
        x=ly['Production_ma'].iloc[-1], y=ly['Stocks_ma'].iloc[-1],
        ax=ly['Production_ma'].iloc[-3], ay=ly['Stocks_ma'].iloc[-3],
        xref='x', yref='y', axref='x', ayref='y',
        showarrow=True, arrowhead=3, arrowsize=1.5, arrowcolor='red'
    )

fig.update_layout(
    title='Production vs Commercial Stocks — Phase Space (13wk MA)',
    xaxis_title='Crude Production (kbd)',
    yaxis_title='Commercial Stocks (kb)',
    height=550, template='plotly_white',
    hovermode='closest'
)
fig.show()

# %% [markdown]
# ---
# ## 12. Weekly Stock Change Decomposition
#
# Decompose the weekly change in crude stocks into its components:
# production, imports, exports, and refinery demand.

# %%
decomp = balance[['Production', 'Imports', 'Exports', 'Refinery Runs', 'Commercial Stocks']].dropna().copy()
decomp['Stock Change'] = decomp['Commercial Stocks'].diff()

# 4-week averages
decomp_ma = decomp.rolling(4).mean().dropna()

# Last 2 years for detail
cutoff = decomp_ma.index.max() - pd.DateOffset(years=2)
recent = decomp_ma[decomp_ma.index >= cutoff]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=recent.index, y=recent['Production'],
    name='Production', marker_color='#22c55e'
))
fig.add_trace(go.Bar(
    x=recent.index, y=recent['Imports'],
    name='Imports', marker_color='#3b82f6'
))
fig.add_trace(go.Bar(
    x=recent.index, y=-recent['Exports'],
    name='Exports', marker_color='#ef4444'
))
fig.add_trace(go.Bar(
    x=recent.index, y=-recent['Refinery Runs'],
    name='Refinery Runs', marker_color='#f59e0b'
))

fig.add_trace(go.Scatter(
    x=recent.index, y=recent['Stock Change'],
    name='Stock Change', line=dict(color='black', width=3),
    mode='lines'
))

fig.update_layout(
    barmode='relative',
    title='Crude Stock Change Decomposition (4wk avg, last 2 years)',
    yaxis_title='kbd',
    height=500, template='plotly_white',
    legend=dict(orientation='h', y=-0.12),
    hovermode='x unified'
)
fig.show()

# %% [markdown]
# ---
# ## 13. Supply Risk Scorecard
#
# Combine multiple metrics into a single country-level risk score for
# US crude import dependence.

# %%
# Build risk scorecard for top source countries
latest_year = cli['YEAR'].max()
prev_year = latest_year - 1

risk_data = []
for country in top_countries:
    c_data = cli[cli['CNTRY_NAME'] == country]
    c_current = c_data[c_data['YEAR'] == latest_year]
    c_prev = c_data[c_data['YEAR'] == prev_year]

    vol_current = c_current['QUANTITY'].sum()
    vol_prev = c_prev['QUANTITY'].sum()
    vol_change = ((vol_current - vol_prev) / vol_prev * 100) if vol_prev > 0 else 0

    # Volatility: coefficient of variation of monthly volumes
    monthly_vols = c_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
    cv = monthly_vols.std() / monthly_vols.mean() * 100 if monthly_vols.mean() > 0 else 0

    # Concentration: how many companies import from this country
    company_count = c_data['R_S_NAME'].nunique()

    # Share of total US imports
    total_vol = cli['QUANTITY'].sum()
    share = vol_current / cli[cli['YEAR'] == latest_year]['QUANTITY'].sum() * 100 if vol_current > 0 else 0

    risk_data.append({
        'Country': country,
        'Import Share (%)': round(share, 1),
        'YoY Volume Change (%)': round(vol_change, 1),
        'Monthly Volatility (CV%)': round(cv, 1),
        'Importer Count': company_count,
        'Avg API': round(c_data['APIGRAVITY'].mean(), 1),
        'Avg Sulfur': round(c_data['SULFUR'].mean(), 2),
    })

risk_df = pd.DataFrame(risk_data)

# Composite risk score (higher = more risk to US supply)
risk_df['Size Risk'] = risk_df['Import Share (%)'] / risk_df['Import Share (%)'].max() * 100
risk_df['Volatility Risk'] = risk_df['Monthly Volatility (CV%)'] / risk_df['Monthly Volatility (CV%)'].max() * 100
risk_df['Concentration Risk'] = (1 - risk_df['Importer Count'] / risk_df['Importer Count'].max()) * 100
risk_df['Risk Score'] = (risk_df['Size Risk'] * 0.4 + risk_df['Volatility Risk'] * 0.3 + risk_df['Concentration Risk'] * 0.3).round(1)

risk_df = risk_df.sort_values('Risk Score', ascending=True)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=risk_df['Country'], x=risk_df['Risk Score'],
    orientation='h',
    marker=dict(
        color=risk_df['Risk Score'],
        colorscale='YlOrRd',
        showscale=True,
        colorbar=dict(title='Risk')
    ),
    text=risk_df['Risk Score'],
    textposition='outside',
    hovertemplate=(
        '<b>%{y}</b><br>'
        'Risk Score: %{x:.1f}<br>'
        'Import Share: %{customdata[0]:.1f}%<br>'
        'Volatility: %{customdata[1]:.1f}%<br>'
        'Importers: %{customdata[2]}<extra></extra>'
    ),
    customdata=risk_df[['Import Share (%)', 'Monthly Volatility (CV%)', 'Importer Count']].values
))

fig.update_layout(
    title='Crude Import Supply Risk Scorecard',
    xaxis_title='Composite Risk Score',
    height=450, template='plotly_white',
    yaxis=dict(autorange='reversed')
)
fig.show()

print(risk_df[['Country', 'Import Share (%)', 'Monthly Volatility (CV%)', 'Importer Count', 'Risk Score']].to_string(index=False))

# %% [markdown]
# ---
# ## 14. The Big Picture — Correlation Matrix of Key Indicators
#
# How do the major petroleum indicators move together?

# %%
# Select key series from WPS
corr_ids = {
    'WCRFPUS2': 'Crude Prod',
    'WCEIMUS2': 'Crude Imports',
    'WCREXUS2': 'Crude Exports',
    'WCRRIUS2': 'Refinery Runs',
    'WCESTUS1': 'Crude Stocks',
    'WGTSTUS1': 'Gasoline Stocks',
    'WDISTUS1': 'Distillate Stocks',
    'WGFRPUS2': 'Gasoline Prod',
    'WPULEUS3': 'Refinery Util',
}

available_corr = {k: v for k, v in corr_ids.items() if k in wps_pivot.columns}
corr_df = wps_pivot[['period'] + list(available_corr.keys())].set_index('period')
corr_df.columns = [available_corr[c] for c in corr_df.columns]

# Use weekly changes (diff) for more meaningful correlation
corr_changes = corr_df.diff().dropna()
corr_matrix = corr_changes.corr()

fig = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_matrix.columns,
    y=corr_matrix.index,
    colorscale='RdBu_r',
    zmid=0, zmin=-1, zmax=1,
    text=corr_matrix.round(2).values,
    texttemplate='%{text}',
    textfont=dict(size=10),
    colorbar=dict(title='Correlation')
))

fig.update_layout(
    title='Weekly Change Correlation Matrix — Key Petroleum Indicators',
    height=550, width=700, template='plotly_white',
    xaxis=dict(tickangle=45)
)
fig.show()

# %% [markdown]
# ---
# ## Summary
#
# This notebook combined three EIA data sources to build a multi-dimensional
# view of the US crude oil market:
#
# - **WPS weekly data** revealed the supply/demand balance, stock dynamics,
#   and how key indicators move together
# - **Company-level import data** exposed the geographic and quality fingerprint
#   of US crude sourcing, importer clustering, and supply risk
# - **DPR forecast data** showed the shale production trajectory and how
#   the outlook has evolved across successive forecasts
#
# The phase space diagram and importer clustering are particularly useful
# for identifying structural regime shifts and market participant behavior.

# %%
print("Notebook complete.")
