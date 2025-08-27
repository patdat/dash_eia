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
regions = ['Permian', 'Bakken', 'Eagle Ford', 'Appalachia', 'Haynesville', 'Rest of L48 ex GOM']

def get_duc_waterfall_data(df_melted, release_date, region):
    """Calculate DUC waterfall data showing flow from drilling to completion"""
    # Filter for specific release and region
    df_filtered = df_melted[
        (df_melted['release_date'] == release_date) & 
        (df_melted['region'] == region)
    ].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Get region abbreviation
    region_abbrev = {
        'Permian': 'PM', 'Bakken': 'BK', 'Eagle Ford': 'EF',
        'Appalachia': 'AP', 'Haynesville': 'HA', 'Rest of L48 ex GOM': 'R48'
    }.get(region, '')
    
    if not region_abbrev:
        return pd.DataFrame()
    
    # Create pivot table for this region
    pivot_data = df_filtered.pivot_table(
        index='delivery_month',
        columns='id',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Get relevant columns
    wells_drilled_col = f'NWD{region_abbrev}'
    wells_completed_col = f'NWC{region_abbrev}'
    ducs_col = f'DUCS{region_abbrev}'
    
    waterfall_data = []
    
    for _, row in pivot_data.iterrows():
        month = row['delivery_month']
        wells_drilled = row.get(wells_drilled_col, 0) or 0
        wells_completed = row.get(wells_completed_col, 0) or 0
        ducs_inventory = row.get(ducs_col, 0) or 0
        
        waterfall_data.append({
            'month': month,
            'wells_drilled': wells_drilled,
            'wells_completed': wells_completed,
            'ducs_inventory': ducs_inventory,
            'duc_change': wells_drilled - wells_completed
        })
    
    return pd.DataFrame(waterfall_data)

def create_duc_waterfall_chart(waterfall_df, region):
    """Create waterfall chart showing DUC inventory changes"""
    if waterfall_df.empty:
        return go.Figure()
    
    # Sort by month
    waterfall_df = waterfall_df.sort_values('month')
    
    # Create waterfall chart
    fig = go.Figure()
    
    # Add wells drilled (positive)
    fig.add_trace(go.Bar(
        name='Wells Drilled',
        x=waterfall_df['month'],
        y=waterfall_df['wells_drilled'],
        marker_color='lightblue',
        hovertemplate='<b>Wells Drilled</b><br>' +
                     'Month: %{x}<br>' +
                     'Count: %{y}<br>' +
                     '<extra></extra>'
    ))
    
    # Add wells completed (negative)
    fig.add_trace(go.Bar(
        name='Wells Completed',
        x=waterfall_df['month'],
        y=-waterfall_df['wells_completed'],
        marker_color='lightcoral',
        hovertemplate='<b>Wells Completed</b><br>' +
                     'Month: %{x}<br>' +
                     'Count: %{y}<br>' +
                     '<extra></extra>'
    ))
    
    # Add DUC inventory line
    fig.add_trace(go.Scatter(
        name='DUC Inventory',
        x=waterfall_df['month'],
        y=waterfall_df['ducs_inventory'],
        mode='lines+markers',
        line=dict(color='darkgreen', width=3),
        marker=dict(size=8),
        yaxis='y2',
        hovertemplate='<b>DUC Inventory</b><br>' +
                     'Month: %{x}<br>' +
                     'Count: %{y}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'{region} - DUC Inventory Waterfall Analysis',
        xaxis_title='Month',
        yaxis_title='Wells Drilled/Completed (Monthly)',
        yaxis2=dict(
            title='DUC Inventory (Cumulative)',
            overlaying='y',
            side='right'
        ),
        barmode='relative',
        height=500,
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_regional_duc_comparison(df_melted, release_date, month):
    """Create comparison chart of DUC metrics across regions"""
    month_dt = pd.to_datetime(month)
    
    # Filter for specific release and month
    df_filtered = df_melted[
        (df_melted['release_date'] == release_date) & 
        (df_melted['delivery_month'] == month_dt)
    ].copy()
    
    if df_filtered.empty:
        return go.Figure()
    
    # Create pivot table
    pivot_data = df_filtered.pivot_table(
        index='region',
        columns='id',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    comparison_data = []
    
    for _, row in pivot_data.iterrows():
        region = row['region']
        
        if region not in regions:
            continue
            
        region_abbrev = {
            'Permian': 'PM', 'Bakken': 'BK', 'Eagle Ford': 'EF',
            'Appalachia': 'AP', 'Haynesville': 'HA', 'Rest of L48 ex GOM': 'R48'
        }.get(region, '')
        
        if region_abbrev:
            wells_drilled = row.get(f'NWD{region_abbrev}', 0) or 0
            wells_completed = row.get(f'NWC{region_abbrev}', 0) or 0
            ducs = row.get(f'DUCS{region_abbrev}', 0) or 0
            
            comparison_data.append({
                'region': region,
                'wells_drilled': wells_drilled,
                'wells_completed': wells_completed,
                'ducs_inventory': ducs,
                'completion_rate': wells_completed / max(wells_drilled, 1) if wells_drilled > 0 else 0
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    if comparison_df.empty:
        return go.Figure()
    
    # Create grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Wells Drilled',
        x=comparison_df['region'],
        y=comparison_df['wells_drilled'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Wells Completed',
        x=comparison_df['region'],
        y=comparison_df['wells_completed'],
        marker_color='lightcoral'
    ))
    
    fig.add_trace(go.Bar(
        name='DUC Inventory',
        x=comparison_df['region'],
        y=comparison_df['ducs_inventory'],
        marker_color='darkgreen'
    ))
    
    fig.update_layout(
        title=f'Regional DUC Comparison - {month_dt.strftime("%Y-%m")}',
        xaxis_title='Region',
        yaxis_title='Well Count',
        barmode='group',
        height=400
    )
    
    return fig

# Layout
layout = html.Div([
    html.H1("DUC Inventory Waterfall Analysis", style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Controls
    html.Div([
        html.Div([
            html.Label("Release Date:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-8-release-dropdown',
                options=[{'label': d.strftime('%Y-%m-%d'), 'value': d.isoformat()} for d in release_dates],
                value=release_dates[0].isoformat() if release_dates else None,
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Region:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-8-region-dropdown',
                options=[{'label': region, 'value': region} for region in regions],
                value='Permian',
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Comparison Month:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-8-month-dropdown',
                options=[],  # Will be populated by callback
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block'})
    ], style={'textAlign': 'center', 'marginBottom': 30}),
    
    # DUC Waterfall Chart
    html.Div([
        html.H3("DUC Inventory Flow", style={'textAlign': 'center'}),
        dcc.Graph(id='page3-8-duc-waterfall', style={'height': '600px'})
    ], style={'marginBottom': 40}),
    
    # Regional Comparison
    html.Div([
        html.H3("Regional DUC Comparison", style={'textAlign': 'center'}),
        dcc.Graph(id='page3-8-regional-comparison', style={'height': '500px'})
    ])
])

@callback(
    Output('page3-8-month-dropdown', 'options'),
    Input('page3-8-release-dropdown', 'value')
)
def update_month_options(release_date_str):
    if not release_date_str:
        return []
    
    release_date = pd.to_datetime(release_date_str)
    
    # Get available months for this release
    available_months = df_melted[
        df_melted['release_date'] == release_date
    ]['delivery_month'].unique()
    
    options = [
        {'label': pd.to_datetime(month).strftime('%Y-%m'), 'value': month.isoformat()}
        for month in sorted(available_months)  # Show all available months
    ]
    
    return options

@callback(
    [Output('page3-8-duc-waterfall', 'figure'),
     Output('page3-8-regional-comparison', 'figure')],
    [Input('page3-8-release-dropdown', 'value'),
     Input('page3-8-region-dropdown', 'value'),
     Input('page3-8-month-dropdown', 'value')]
)
def update_duc_analysis(release_date_str, region, month_str):
    if not release_date_str or not region:
        return go.Figure(), go.Figure()
    
    release_date = pd.to_datetime(release_date_str)
    
    # Get waterfall data
    waterfall_df = get_duc_waterfall_data(df_melted, release_date, region)
    waterfall_fig = create_duc_waterfall_chart(waterfall_df, region)
    
    # Get regional comparison if month is selected
    comparison_fig = go.Figure()
    if month_str:
        comparison_fig = create_regional_duc_comparison(df_melted, release_date, month_str)
    
    return waterfall_fig, comparison_fig