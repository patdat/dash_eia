from dash import html, dcc, callback, Output, Input, ctx, State
import dash_ag_grid as dag
import dash_daq as daq
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
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

def get_radar_chart_data(df_melted, release_date, month):
    """Calculate multi-dimensional performance metrics for radar chart"""
    month_dt = pd.to_datetime(month)
    
    # Filter for specific release and month
    df_filtered = df_melted[
        (df_melted['release_date'] == release_date) & 
        (df_melted['delivery_month'] == month_dt)
    ].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Create pivot table
    pivot_data = df_filtered.pivot_table(
        index='region',
        columns='id',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    radar_data = []
    
    for _, row in pivot_data.iterrows():
        region = row['region']
        
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
            
            # Calculate normalized performance metrics (0-100 scale)
            production_per_rig = production / max(rigs, 1)
            wells_per_rig = wells_drilled / max(rigs, 1)
            completion_rate = (wells_completed / max(wells_drilled, 1)) * 100 if wells_drilled > 0 else 0
            duc_efficiency = max(0, 100 - (ducs / max(wells_drilled, 1)) * 100) if wells_drilled > 0 else 0
            new_well_productivity = new_well_prod / max(wells_completed, 1) if wells_completed > 0 else 0
            rig_utilization = min(100, (wells_drilled / max(rigs * 12, 1)) * 100)  # Assuming 12 wells/rig/year max
            
            radar_data.append({
                'region': region,
                'production_per_rig': production_per_rig,
                'wells_per_rig': wells_per_rig,
                'completion_rate': completion_rate,
                'duc_efficiency': duc_efficiency,
                'new_well_productivity': new_well_productivity,
                'rig_utilization': rig_utilization,
                'total_production': production,
                'total_rigs': rigs
            })
    
    return pd.DataFrame(radar_data)

def normalize_radar_metrics(radar_df):
    """Normalize metrics to 0-100 scale for radar chart"""
    if radar_df.empty:
        return pd.DataFrame()
    
    normalized_df = radar_df.copy()
    
    # Metrics to normalize (excluding categorical and already normalized ones)
    metrics_to_normalize = ['production_per_rig', 'wells_per_rig', 'new_well_productivity', 'rig_utilization']
    
    for metric in metrics_to_normalize:
        if metric in normalized_df.columns:
            min_val = normalized_df[metric].min()
            max_val = normalized_df[metric].max()
            if max_val > min_val:
                normalized_df[f'{metric}_normalized'] = ((normalized_df[metric] - min_val) / (max_val - min_val)) * 100
            else:
                normalized_df[f'{metric}_normalized'] = 50  # If all values are same, set to middle
    
    return normalized_df

def create_radar_chart(radar_df):
    """Create radar chart comparing regional performance"""
    if radar_df.empty:
        return go.Figure()
    
    # Normalize the data
    normalized_df = normalize_radar_metrics(radar_df)
    
    # Define the radar chart categories
    categories = [
        'Production per Rig',
        'Wells per Rig', 
        'Completion Rate',
        'DUC Efficiency',
        'New Well Productivity',
        'Rig Utilization'
    ]
    
    category_mappings = {
        'Production per Rig': 'production_per_rig_normalized',
        'Wells per Rig': 'wells_per_rig_normalized',
        'Completion Rate': 'completion_rate',
        'DUC Efficiency': 'duc_efficiency',
        'New Well Productivity': 'new_well_productivity_normalized',
        'Rig Utilization': 'rig_utilization_normalized'
    }
    
    fig = go.Figure()
    
    # Color palette for regions
    colors = px.colors.qualitative.Set3
    
    for i, region in enumerate(regions):
        if region not in normalized_df['region'].values:
            continue
            
        region_data = normalized_df[normalized_df['region'] == region].iloc[0]
        
        # Get values for each category
        values = []
        for category in categories:
            col_name = category_mappings[category]
            if col_name in region_data:
                values.append(region_data[col_name])
            else:
                values.append(0)
        
        # Close the radar chart by repeating the first value
        values.append(values[0])
        categories_closed = categories + [categories[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories_closed,
            fill='toself',
            name=region,
            line_color=colors[i % len(colors)],
            fillcolor=colors[i % len(colors)],
            opacity=0.3
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='%'
            )
        ),
        showlegend=True,
        title="Regional Performance Radar Chart",
        height=600
    )
    
    return fig

def create_performance_ranking_chart(radar_df):
    """Create a horizontal bar chart showing overall performance ranking"""
    if radar_df.empty:
        return go.Figure()
    
    # Calculate composite performance score
    normalized_df = normalize_radar_metrics(radar_df)
    
    metrics = ['production_per_rig_normalized', 'wells_per_rig_normalized', 'completion_rate', 
              'duc_efficiency', 'new_well_productivity_normalized', 'rig_utilization_normalized']
    
    # Calculate average score across all metrics
    normalized_df['composite_score'] = normalized_df[metrics].mean(axis=1)
    
    # Sort by composite score
    sorted_df = normalized_df.sort_values('composite_score', ascending=True)
    
    fig = go.Figure()
    
    # Create horizontal bar chart
    fig.add_trace(go.Bar(
        x=sorted_df['composite_score'],
        y=sorted_df['region'],
        orientation='h',
        marker_color='lightblue',
        text=sorted_df['composite_score'].round(1),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>' +
                     'Composite Score: %{x:.1f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title="Regional Performance Ranking (Composite Score)",
        xaxis_title="Performance Score (0-100)",
        yaxis_title="Region",
        height=400,
        margin=dict(l=150, r=50, t=50, b=50)
    )
    
    return fig

def create_metric_comparison_chart(radar_df, selected_regions):
    """Create detailed metric comparison for selected regions"""
    if radar_df.empty or not selected_regions:
        return go.Figure()
    
    # Filter for selected regions
    filtered_df = radar_df[radar_df['region'].isin(selected_regions)]
    
    if filtered_df.empty:
        return go.Figure()
    
    # Metrics to compare
    metrics = [
        ('production_per_rig', 'Production per Rig (mbd)'),
        ('wells_per_rig', 'Wells per Rig'),
        ('completion_rate', 'Completion Rate (%)'),
        ('duc_efficiency', 'DUC Efficiency (%)'),
        ('new_well_productivity', 'New Well Productivity'),
        ('rig_utilization', 'Rig Utilization (%)')
    ]
    
    fig = go.Figure()
    
    for metric_col, metric_name in metrics:
        for region in selected_regions:
            region_data = filtered_df[filtered_df['region'] == region]
            if not region_data.empty:
                value = region_data[metric_col].iloc[0]
                fig.add_trace(go.Bar(
                    name=f"{region} - {metric_name}",
                    x=[metric_name],
                    y=[value],
                    showlegend=False,
                    text=f"{value:.1f}",
                    textposition='outside'
                ))
    
    fig.update_layout(
        title=f"Detailed Metrics Comparison - {', '.join(selected_regions)}",
        xaxis_title="Metrics",
        yaxis_title="Values",
        height=500,
        barmode='group'
    )
    
    return fig

# Layout
layout = html.Div([
    html.H1("Regional Performance Radar Analysis", style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Controls
    html.Div([
        html.Div([
            html.Label("Release Date:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-10-release-dropdown',
                options=[{'label': d.strftime('%Y-%m-%d'), 'value': d.isoformat()} for d in release_dates],
                value=release_dates[0].isoformat() if release_dates else None,
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Analysis Month:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-10-month-dropdown',
                options=[],  # Will be populated by callback
                style={'width': '200px'}
            )
        ], style={'display': 'inline-block', 'marginRight': 20}),
        
        html.Div([
            html.Label("Regions for Comparison:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.Dropdown(
                id='page3-10-region-multi-dropdown',
                options=[{'label': region, 'value': region} for region in regions],
                value=['Permian', 'Bakken'],
                multi=True,
                style={'width': '300px'}
            )
        ], style={'display': 'inline-block'})
    ], style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Radar Chart
    html.Div([
        html.H3("Multi-Dimensional Performance Radar", style={'textAlign': 'center'}),
        dcc.Graph(id='page3-10-radar-chart', style={'height': '700px'})
    ], style={'marginBottom': 40}),
    
    # Performance Ranking
    html.Div([
        html.Div([
            html.H3("Performance Ranking", style={'textAlign': 'center'}),
            dcc.Graph(id='page3-10-ranking-chart', style={'height': '500px'})
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            html.H3("Detailed Metrics Comparison", style={'textAlign': 'center'}),
            dcc.Graph(id='page3-10-comparison-chart', style={'height': '500px'})
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ])
])

@callback(
    [Output('page3-10-month-dropdown', 'options'),
     Output('page3-10-month-dropdown', 'value')],
    Input('page3-10-release-dropdown', 'value')
)
def update_month_options(release_date_str):
    if not release_date_str:
        return [], None
    
    release_date = pd.to_datetime(release_date_str)
    
    # Get available months for this release
    available_months = df_melted[
        df_melted['release_date'] == release_date
    ]['delivery_month'].unique()
    
    options = [
        {'label': pd.to_datetime(month).strftime('%Y-%m'), 'value': month.isoformat()}
        for month in sorted(available_months)  # Show all available months
    ]
    
    # Set default value to the most recent month
    default_value = sorted(available_months)[-1].isoformat() if len(available_months) > 0 else None
    
    return options, default_value

@callback(
    [Output('page3-10-radar-chart', 'figure'),
     Output('page3-10-ranking-chart', 'figure'),
     Output('page3-10-comparison-chart', 'figure')],
    [Input('page3-10-release-dropdown', 'value'),
     Input('page3-10-month-dropdown', 'value'),
     Input('page3-10-region-multi-dropdown', 'value')]
)
def update_radar_analysis(release_date_str, month_str, selected_regions):
    if not release_date_str or not month_str:
        return go.Figure(), go.Figure(), go.Figure()
    
    release_date = pd.to_datetime(release_date_str)
    
    # Get radar chart data
    radar_df = get_radar_chart_data(df_melted, release_date, month_str)
    
    if radar_df.empty:
        return go.Figure(), go.Figure(), go.Figure()
    
    # Create radar chart
    radar_fig = create_radar_chart(radar_df)
    
    # Create ranking chart
    ranking_fig = create_performance_ranking_chart(radar_df)
    
    # Create comparison chart
    comparison_fig = create_metric_comparison_chart(radar_df, selected_regions)
    
    return radar_fig, ranking_fig, comparison_fig