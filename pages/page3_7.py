from dash import html, dcc, callback, Output, Input, ctx, State
import dash_ag_grid as dag
import dash_daq as daq
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.data_loader import cached_loader

# Load data and mapping
df = cached_loader.load_steo_dpr_data()
mapping_df = cached_loader.load_dpr_mapping()

# Get date columns (all columns that are not metadata)
metadata_cols = ['id', 'name', 'release_date', 'uom']
date_columns = [col for col in df.columns if col not in metadata_cols]

# Melt the dataframe to have delivery_month as a column
df_melted = pd.melt(df, 
                    id_vars=metadata_cols,
                    value_vars=date_columns,
                    var_name='delivery_month',
                    value_name='value')

# Convert delivery_month to datetime
df_melted['delivery_month'] = pd.to_datetime(df_melted['delivery_month'])

# Merge with mapping to get region information
df_melted = df_melted.merge(mapping_df[['id', 'region']], on='id', how='left')

# Get unique release dates sorted (most recent first)
release_dates = sorted(df_melted['release_date'].unique(), reverse=True)

def calculate_efficiency_metrics(df_melted, release_date):
    """Calculate efficiency metrics by region and time"""
    # Filter for specific release
    df_filtered = df_melted[df_melted['release_date'] == release_date].copy()
    
    # Create pivot tables for different metrics
    pivot_data = df_filtered.pivot_table(
        index=['delivery_month', 'region'],
        columns='id',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Calculate efficiency metrics
    efficiency_metrics = []
    
    for _, row in pivot_data.iterrows():
        region = row['region']
        month = row['delivery_month']
        
        # Skip non-region rows
        if pd.isna(region) or region in ['United States', 'Aalaska', 'Gulf of Mexico', 'L48 ex GOM']:
            continue
            
        # Find production and rig columns for this region
        region_abbrev = {
            'Permian': 'PM', 'Bakken': 'BK', 'Eagle Ford': 'EF',
            'Appalachia': 'AP', 'Haynesville': 'HA', 'Rest of L48 ex GOM': 'R48'
        }.get(region, '')
        
        if region_abbrev:
            prod_col = f'COPR{region_abbrev}'
            rig_col = f'RIGS{region_abbrev}'
            wells_drilled_col = f'NWD{region_abbrev}'
            wells_completed_col = f'NWC{region_abbrev}'
            ducs_col = f'DUCS{region_abbrev}'
            
            production = row.get(prod_col, 0) or 0
            rigs = row.get(rig_col, 1) or 1  # Avoid division by zero
            wells_drilled = row.get(wells_drilled_col, 0) or 0
            wells_completed = row.get(wells_completed_col, 0) or 0
            ducs = row.get(ducs_col, 0) or 0
            
            # Calculate various efficiency metrics
            prod_per_rig = production / max(rigs, 1)
            wells_per_rig = wells_drilled / max(rigs, 1)
            completion_rate = wells_completed / max(wells_drilled, 1) if wells_drilled > 0 else 0
            duc_ratio = ducs / max(wells_drilled, 1) if wells_drilled > 0 else 0
            
            efficiency_metrics.append({
                'region': region,
                'month': month,
                'production_per_rig': prod_per_rig,
                'wells_per_rig': wells_per_rig,
                'completion_rate': completion_rate,
                'duc_ratio': duc_ratio,
                'total_production': production,
                'total_rigs': rigs
            })
    
    return pd.DataFrame(efficiency_metrics)

def create_efficiency_heatmap(efficiency_df, metric='production_per_rig'):
    """Create heatmap for efficiency metrics"""
    if efficiency_df.empty:
        return go.Figure()
    
    # Pivot for heatmap
    heatmap_data = efficiency_df.pivot_table(
        index='region',
        columns='month',
        values=metric,
        aggfunc='mean'
    )
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[d.strftime('%Y-%m') for d in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale='RdYlGn',
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>' +
                     'Month: %{x}<br>' +
                     f'{metric.replace("_", " ").title()}: %{{z:.2f}}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'{metric.replace("_", " ").title()} by Region and Time',
        xaxis_title='Month',
        yaxis_title='Region',
        height=500,
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    return fig

# Layout
layout = html.Div([
    html.H1("Advanced DPR Analytics - Regional Efficiency", style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Controls
    html.Div([
        html.Div([
            html.Label("Release Date:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-7-release-dropdown',
                options=[{'label': d.strftime('%Y-%m-%d'), 'value': d.isoformat()} for d in release_dates],
                value=release_dates[0].isoformat() if release_dates else None,
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Efficiency Metric:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-7-metric-dropdown',
                options=[
                    {'label': 'Production per Rig', 'value': 'production_per_rig'},
                    {'label': 'Wells per Rig', 'value': 'wells_per_rig'},
                    {'label': 'Completion Rate', 'value': 'completion_rate'},
                    {'label': 'DUC Ratio', 'value': 'duc_ratio'}
                ],
                value='production_per_rig',
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block'})
    ], style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Efficiency Heatmap
    html.Div([
        html.H3("Regional Efficiency Heatmap", style={'textAlign': 'center'}),
        dcc.Graph(id='page3-7-efficiency-heatmap', style={'height': '600px'})
    ], style={'marginBottom': 40}),
    
    # Summary Statistics
    html.Div([
        html.H3("Efficiency Summary", style={'textAlign': 'center'}),
        html.Div(id='page3-7-efficiency-summary', style={'textAlign': 'center'})
    ])
])

@callback(
    [Output('page3-7-efficiency-heatmap', 'figure'),
     Output('page3-7-efficiency-summary', 'children')],
    [Input('page3-7-release-dropdown', 'value'),
     Input('page3-7-metric-dropdown', 'value')]
)
def update_efficiency_analysis(release_date_str, metric):
    if not release_date_str:
        return go.Figure(), ""
    
    release_date = pd.to_datetime(release_date_str)
    
    # Calculate efficiency metrics
    efficiency_df = calculate_efficiency_metrics(df_melted, release_date)
    
    if efficiency_df.empty:
        return go.Figure(), "No data available for selected parameters."
    
    # Create heatmap
    heatmap_fig = create_efficiency_heatmap(efficiency_df, metric)
    
    # Create summary statistics
    metric_stats = efficiency_df.groupby('region')[metric].agg(['mean', 'std', 'min', 'max'])
    
    summary_cards = []
    for region, stats in metric_stats.iterrows():
        card = html.Div([
            html.H4(region, style={'marginBottom': 10}),
            html.P([
                html.Strong("Avg: "), f"{stats['mean']:.2f}", html.Br(),
                html.Strong("Range: "), f"{stats['min']:.2f} - {stats['max']:.2f}", html.Br(),
                html.Strong("Std: "), f"{stats['std']:.2f}"
            ])
        ], style={
            'border': '1px solid #ddd',
            'borderRadius': '5px',
            'padding': '15px',
            'margin': '10px',
            'backgroundColor': '#f9f9f9',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'width': '200px'
        })
        summary_cards.append(card)
    
    summary_div = html.Div(summary_cards, style={'textAlign': 'center'})
    
    return heatmap_fig, summary_div