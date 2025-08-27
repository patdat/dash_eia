from dash import html, dcc, callback, Output, Input, ctx, State
import dash_ag_grid as dag
import dash_daq as daq
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
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
regions = ['Permian', 'Bakken', 'Eagle Ford', 'Appalachia', 'Haynesville', 'Rest of L48 ex GOM']

def get_productivity_matrix_data(df_melted, release_date):
    """Calculate productivity matrix data for scatter plot analysis"""
    # Filter for specific release
    df_filtered = df_melted[df_melted['release_date'] == release_date].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Create pivot table
    pivot_data = df_filtered.pivot_table(
        index=['delivery_month', 'region'],
        columns='id',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    productivity_data = []
    
    for _, row in pivot_data.iterrows():
        region = row['region']
        month = row['delivery_month']
        
        if region not in regions:
            continue
            
        # Get region abbreviation
        region_abbrev = {
            'Permian': 'PM', 'Bakken': 'BK', 'Eagle Ford': 'EF',
            'Appalachia': 'AP', 'Haynesville': 'HA', 'Rest of L48 ex GOM': 'R48'
        }.get(region, '')
        
        if region_abbrev:
            production = row.get(f'COPR{region_abbrev}', 0) or 0
            rigs = row.get(f'RIGS{region_abbrev}', 1) or 1
            wells_drilled = row.get(f'NWD{region_abbrev}', 0) or 0
            wells_completed = row.get(f'NWC{region_abbrev}', 0) or 0
            ducs = row.get(f'DUCS{region_abbrev}', 0) or 0
            new_well_prod = row.get(f'CONW{region_abbrev}', 0) or 0
            
            # Calculate productivity metrics
            production_per_rig = production / max(rigs, 1)
            wells_per_rig = wells_drilled / max(rigs, 1)
            production_per_well = production / max(wells_completed, 1) if wells_completed > 0 else 0
            new_well_productivity = new_well_prod / max(wells_completed, 1) if wells_completed > 0 else 0
            rig_efficiency = (wells_drilled * production_per_well) / max(rigs, 1)
            
            productivity_data.append({
                'region': region,
                'month': month,
                'production_per_rig': production_per_rig,
                'wells_per_rig': wells_per_rig,
                'production_per_well': production_per_well,
                'new_well_productivity': new_well_productivity,
                'rig_efficiency': rig_efficiency,
                'total_production': production,
                'total_rigs': rigs,
                'wells_drilled': wells_drilled,
                'wells_completed': wells_completed,
                'ducs_inventory': ducs
            })
    
    return pd.DataFrame(productivity_data)

def create_productivity_scatter(productivity_df, x_metric, y_metric, size_metric, color_metric):
    """Create scatter plot for productivity analysis"""
    if productivity_df.empty:
        return go.Figure()
    
    # Remove rows with zero or NaN values
    clean_df = productivity_df.dropna(subset=[x_metric, y_metric, size_metric, color_metric])
    clean_df = clean_df[(clean_df[x_metric] > 0) & (clean_df[y_metric] > 0)]
    
    if clean_df.empty:
        return go.Figure()
    
    # Normalize size values for better bubble sizing
    scaler = MinMaxScaler(feature_range=(10, 50))
    size_values = scaler.fit_transform(clean_df[[size_metric]].values).flatten()
    
    fig = go.Figure()
    
    # Create scatter plot for each region
    for region in regions:
        region_data = clean_df[clean_df['region'] == region]
        
        if region_data.empty:
            continue
            
        region_sizes = scaler.transform(region_data[[size_metric]].values).flatten()
        
        fig.add_trace(go.Scatter(
            x=region_data[x_metric],
            y=region_data[y_metric],
            mode='markers',
            name=region,
            marker=dict(
                size=region_sizes,
                color=region_data[color_metric],
                colorscale='Viridis',
                showscale=True if region == regions[0] else False,
                colorbar=dict(title=color_metric.replace('_', ' ').title()) if region == regions[0] else None,
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=region_data.apply(lambda row: f"{row['region']}<br>{row['month'].strftime('%Y-%m')}", axis=1),
            hovertemplate='<b>%{text}</b><br>' +
                         f'{x_metric.replace("_", " ").title()}: %{{x:.2f}}<br>' +
                         f'{y_metric.replace("_", " ").title()}: %{{y:.2f}}<br>' +
                         f'{size_metric.replace("_", " ").title()}: %{{marker.size}}<br>' +
                         f'{color_metric.replace("_", " ").title()}: %{{marker.color:.2f}}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'{y_metric.replace("_", " ").title()} vs {x_metric.replace("_", " ").title()}',
        xaxis_title=x_metric.replace('_', ' ').title(),
        yaxis_title=y_metric.replace('_', ' ').title(),
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

def create_efficiency_frontier(productivity_df):
    """Create efficiency frontier analysis chart"""
    if productivity_df.empty:
        return go.Figure()
    
    # Calculate efficiency frontier based on production per rig and wells per rig
    clean_df = productivity_df.dropna(subset=['production_per_rig', 'wells_per_rig'])
    clean_df = clean_df[(clean_df['production_per_rig'] > 0) & (clean_df['wells_per_rig'] > 0)]
    
    if clean_df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add scatter points for each region
    for region in regions:
        region_data = clean_df[clean_df['region'] == region]
        
        if region_data.empty:
            continue
            
        fig.add_trace(go.Scatter(
            x=region_data['wells_per_rig'],
            y=region_data['production_per_rig'],
            mode='markers',
            name=region,
            marker=dict(size=10, opacity=0.7),
            text=region_data.apply(lambda row: f"{row['region']}<br>{row['month'].strftime('%Y-%m')}", axis=1),
            hovertemplate='<b>%{text}</b><br>' +
                         'Wells per Rig: %{x:.2f}<br>' +
                         'Production per Rig: %{y:.2f}<br>' +
                         '<extra></extra>'
        ))
    
    # Calculate and add efficiency frontier line
    # Sort by wells per rig and find the maximum production per rig for each level
    frontier_data = clean_df.groupby(pd.cut(clean_df['wells_per_rig'], bins=20))['production_per_rig'].max().reset_index()
    frontier_data = frontier_data.dropna()
    
    if len(frontier_data) > 1:
        fig.add_trace(go.Scatter(
            x=[interval.mid for interval in frontier_data['wells_per_rig']],
            y=frontier_data['production_per_rig'],
            mode='lines',
            name='Efficiency Frontier',
            line=dict(color='red', width=3, dash='dash'),
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title='Regional Drilling Efficiency Frontier',
        xaxis_title='Wells per Rig',
        yaxis_title='Production per Rig (mbd)',
        height=500,
        showlegend=True
    )
    
    return fig

# Layout
layout = html.Div([
    html.H1("Drilling Productivity Matrix Analysis", style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Controls
    html.Div([
        html.Div([
            html.Label("Release Date:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-9-release-dropdown',
                options=[{'label': d.strftime('%Y-%m-%d'), 'value': d.isoformat()} for d in release_dates],
                value=release_dates[0].isoformat() if release_dates else None,
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("X-Axis Metric:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-9-x-metric-dropdown',
                options=[
                    {'label': 'Wells per Rig', 'value': 'wells_per_rig'},
                    {'label': 'Production per Rig', 'value': 'production_per_rig'},
                    {'label': 'Production per Well', 'value': 'production_per_well'},
                    {'label': 'Total Rigs', 'value': 'total_rigs'}
                ],
                value='wells_per_rig',
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Y-Axis Metric:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-9-y-metric-dropdown',
                options=[
                    {'label': 'Production per Rig', 'value': 'production_per_rig'},
                    {'label': 'Wells per Rig', 'value': 'wells_per_rig'},
                    {'label': 'Production per Well', 'value': 'production_per_well'},
                    {'label': 'New Well Productivity', 'value': 'new_well_productivity'}
                ],
                value='production_per_rig',
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Bubble Size:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-9-size-metric-dropdown',
                options=[
                    {'label': 'Total Production', 'value': 'total_production'},
                    {'label': 'Total Rigs', 'value': 'total_rigs'},
                    {'label': 'Wells Drilled', 'value': 'wells_drilled'},
                    {'label': 'DUC Inventory', 'value': 'ducs_inventory'}
                ],
                value='total_production',
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Color Metric:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-9-color-metric-dropdown',
                options=[
                    {'label': 'Rig Efficiency', 'value': 'rig_efficiency'},
                    {'label': 'New Well Productivity', 'value': 'new_well_productivity'},
                    {'label': 'Production per Well', 'value': 'production_per_well'},
                    {'label': 'Wells per Rig', 'value': 'wells_per_rig'}
                ],
                value='rig_efficiency',
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block'})
    ], style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Productivity Matrix Scatter Plot
    html.Div([
        html.H3("Productivity Matrix Scatter Plot", style={'textAlign': 'center'}),
        dcc.Graph(id='page3-9-productivity-scatter', style={'height': '700px'})
    ], style={'marginBottom': 40}),
    
    # Efficiency Frontier
    html.Div([
        html.H3("Drilling Efficiency Frontier", style={'textAlign': 'center'}),
        dcc.Graph(id='page3-9-efficiency-frontier', style={'height': '600px'})
    ])
])

@callback(
    [Output('page3-9-productivity-scatter', 'figure'),
     Output('page3-9-efficiency-frontier', 'figure')],
    [Input('page3-9-release-dropdown', 'value'),
     Input('page3-9-x-metric-dropdown', 'value'),
     Input('page3-9-y-metric-dropdown', 'value'),
     Input('page3-9-size-metric-dropdown', 'value'),
     Input('page3-9-color-metric-dropdown', 'value')]
)
def update_productivity_analysis(release_date_str, x_metric, y_metric, size_metric, color_metric):
    if not release_date_str:
        return go.Figure(), go.Figure()
    
    release_date = pd.to_datetime(release_date_str)
    
    # Get productivity data
    productivity_df = get_productivity_matrix_data(df_melted, release_date)
    
    if productivity_df.empty:
        return go.Figure(), go.Figure()
    
    # Create scatter plot
    scatter_fig = create_productivity_scatter(productivity_df, x_metric, y_metric, size_metric, color_metric)
    
    # Create efficiency frontier
    frontier_fig = create_efficiency_frontier(productivity_df)
    
    return scatter_fig, frontier_fig