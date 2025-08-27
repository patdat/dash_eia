import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format
import plotly.graph_objects as go
import plotly.express as px
from src.cli.cli_data_processor import CLIDataProcessor
from datetime import datetime, timedelta
from app import app

processor = CLIDataProcessor()

def generate_port_summary_table(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate monthly aggregates first
    monthly_by_port = filtered_processor.df.groupby(['PORT_CITY', 'RPT_PERIOD'])['QUANTITY'].sum().reset_index()
    
    # Get port-level statistics
    port_stats_monthly = monthly_by_port.groupby('PORT_CITY')['QUANTITY'].agg(['sum', 'mean', 'std']).round(1)
    
    # Get other statistics from raw data
    port_stats_other = filtered_processor.df.groupby('PORT_CITY').agg({
        'R_S_NAME': 'nunique',
        'CNTRY_NAME': 'nunique',
        'APIGRAVITY': 'mean',
        'SULFUR': 'mean'
    }).round(1)
    
    # Combine statistics
    port_stats = pd.concat([port_stats_monthly, port_stats_other], axis=1)
    port_stats.columns = ['Total kbd', 'Avg Monthly kbd', 'Monthly Std Dev', 'Companies', 'Countries', 'Avg API', 'Avg Sulfur']
    port_stats = port_stats.sort_values('Total kbd', ascending=False).head(15)
    
    # Calculate utilization (as % of max month)
    max_month = monthly_by_port.groupby('PORT_CITY')['QUANTITY'].max()
    port_stats['Utilization %'] = (port_stats['Avg Monthly kbd'] / max_month * 100).round(1)
    
    port_stats = port_stats.reset_index()
    
    return dash_table.DataTable(
        data=port_stats.to_dict('records'),
        columns=[
            {"name": "Port", "id": "PORT_CITY"},
            {"name": "Total Volume (kbd)", "id": "Total kbd", "type": "numeric", "format": Format(precision=1)},
            {"name": "Avg Monthly (kbd)", "id": "Avg Monthly kbd", "type": "numeric", "format": Format(precision=1)},
            {"name": "Volatility", "id": "Monthly Std Dev", "type": "numeric", "format": Format(precision=1)},
            {"name": "Companies", "id": "Companies"},
            {"name": "Countries", "id": "Countries"},
            {"name": "Avg API", "id": "Avg API", "type": "numeric", "format": Format(precision=1)},
            {"name": "Avg Sulfur %", "id": "Avg Sulfur", "type": "numeric", "format": Format(precision=2)},
            {"name": "Utilization %", "id": "Utilization %", "type": "numeric", "format": Format(precision=1)}
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
                    'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '11px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Utilization %', 'filter_query': '{Utilization %} > 80'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c'
            },
            {
                'if': {'column_id': 'Utilization %', 'filter_query': '{Utilization %} < 50'},
                'backgroundColor': '#c8e6c9',
                'color': '#1b5e20'
            }
        ],
        page_size=15,
        sort_action='native'
    )

def create_port_volume_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get top 10 ports
    top_ports = filtered_processor.df.groupby('PORT_CITY')['QUANTITY'].sum().nlargest(10).index
    
    fig = go.Figure()
    
    for port in top_ports:
        port_data = filtered_processor.df[filtered_processor.df['PORT_CITY'] == port]
        monthly = port_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly.values,
            mode='lines',
            name=port[:30],
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title='Top 10 Ports - Monthly Import Volumes',
        xaxis_title='Date',
        yaxis_title='Volume (kbd)',
        template='plotly_white',
        height=450,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )
    
    return dcc.Graph(figure=fig)

def create_port_efficiency_scatter(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate port efficiency metrics
    port_metrics = []
    for port in filtered_processor.df['PORT_CITY'].unique():
        port_data = filtered_processor.df[filtered_processor.df['PORT_CITY'] == port]
        
        total_volume = port_data['QUANTITY'].sum()
        num_companies = port_data['R_S_NAME'].nunique()
        num_countries = port_data['CNTRY_NAME'].nunique()
        avg_api = port_data['APIGRAVITY'].mean()
        
        # Efficiency score: volume per company (higher = more concentrated)
        efficiency = total_volume / num_companies if num_companies > 0 else 0
        
        port_metrics.append({
            'Port': port,
            'Volume': total_volume,
            'Companies': num_companies,
            'Countries': num_countries,
            'Efficiency': efficiency,
            'API': avg_api
        })
    
    metrics_df = pd.DataFrame(port_metrics)
    metrics_df = metrics_df[metrics_df['Volume'] > 100]  # Filter small ports
    
    fig = go.Figure(go.Scatter(
        x=metrics_df['Companies'],
        y=metrics_df['Volume'],
        mode='markers+text',
        marker=dict(
            size=metrics_df['Countries'] * 3,
            color=metrics_df['Efficiency'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Efficiency<br>(kbd/Company)'),
            line=dict(width=1, color='white')
        ),
        text=metrics_df['Port'].str[:15],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Volume: %{y:.0f} kbd<br>Companies: %{x}<br><extra></extra>'
    ))
    
    fig.update_layout(
        title='Port Efficiency Analysis (Bubble Size = Country Diversity)',
        xaxis_title='Number of Companies',
        yaxis_title='Total Volume (kbd)',
        template='plotly_white',
        height=450,
        yaxis_type='log'
    )
    
    return dcc.Graph(figure=fig)

def create_port_quality_heatmap(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get top ports and countries
    top_ports = filtered_processor.df.groupby('PORT_CITY')['QUANTITY'].sum().nlargest(10).index
    top_countries = filtered_processor.df.groupby('CNTRY_NAME')['QUANTITY'].sum().nlargest(10).index
    
    # Create matrix
    matrix_data = []
    for port in top_ports:
        row_data = []
        for country in top_countries:
            volume = filtered_processor.df[
                (filtered_processor.df['PORT_CITY'] == port) & 
                (filtered_processor.df['CNTRY_NAME'] == country)
            ]['QUANTITY'].sum()
            row_data.append(volume)
        matrix_data.append(row_data)
    
    fig = go.Figure(go.Heatmap(
        z=matrix_data,
        x=[c[:20] for c in top_countries],
        y=[p[:25] for p in top_ports],
        colorscale='YlOrRd',
        text=np.round(matrix_data, 0),
        texttemplate='%{text:.0f}',
        textfont={"size": 9},
        colorbar=dict(title='Volume<br>(kbd)')
    ))
    
    fig.update_layout(
        title='Port-Country Trade Matrix',
        xaxis_title='Country',
        yaxis_title='Port',
        template='plotly_white',
        height=500,
        xaxis_tickangle=-45,
        margin=dict(b=150)
    )
    
    return dcc.Graph(figure=fig)

def create_port_utilization_gauge(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get top 6 ports for gauge charts
    top_ports = filtered_processor.df.groupby('PORT_CITY')['QUANTITY'].sum().nlargest(6).index
    
    fig = go.Figure()
    
    # Create subplots for gauges
    for i, port in enumerate(top_ports):
        port_data = filtered_processor.df[filtered_processor.df['PORT_CITY'] == port]
        
        # Calculate utilization (current month vs max month)
        latest_month = port_data['RPT_PERIOD'].max()
        current_volume = port_data[port_data['RPT_PERIOD'] == latest_month]['QUANTITY'].sum()
        max_volume = port_data.groupby('RPT_PERIOD')['QUANTITY'].sum().max()
        utilization = (current_volume / max_volume * 100) if max_volume > 0 else 0
        
        row = i // 3
        col = i % 3
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=utilization,
            title={'text': port[:20]},
            domain={'x': [col * 0.33, (col + 1) * 0.33 - 0.05], 
                   'y': [0.5 - row * 0.5, 1 - row * 0.5]},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
    
    fig.update_layout(
        title='Port Utilization Indicators (Current vs Max)',
        template='plotly_white',
        height=400
    )
    
    return dcc.Graph(figure=fig)

def create_port_padd_distribution(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get PADD distribution
    padd_volumes = filtered_processor.df.groupby('PORT_PADD')['QUANTITY'].sum()
    
    # Count ports per PADD
    ports_per_padd = filtered_processor.df.groupby('PORT_PADD')['PORT_CITY'].nunique()
    
    fig = go.Figure()
    
    # Create bubble chart
    fig.add_trace(go.Scatter(
        x=[f'PADD {i}' for i in padd_volumes.index],
        y=padd_volumes.values,
        mode='markers+text',
        marker=dict(
            size=ports_per_padd.values * 10,
            color=padd_volumes.values,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Volume<br>(kbd)'),
            line=dict(width=2, color='white')
        ),
        text=[f'{p} ports' for p in ports_per_padd.values],
        textposition='top center',
        hovertemplate='<b>%{x}</b><br>Volume: %{y:.0f} kbd<br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title='PADD Import Volume and Port Count',
        xaxis_title='PADD Region',
        yaxis_title='Total Volume (kbd)',
        template='plotly_white',
        height=400
    )
    
    return dcc.Graph(figure=fig)

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Port Analysis & Performance',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-port',
                options=[
                    {'label': 'All US', 'value': 'US'},
                    {'label': 'PADD 1 - East Coast', 'value': 'PADD 1'},
                    {'label': 'PADD 2 - Midwest', 'value': 'PADD 2'},
                    {'label': 'PADD 3 - Gulf Coast', 'value': 'PADD 3'},
                    {'label': 'PADD 4 - Rocky Mountain', 'value': 'PADD 4'},
                    {'label': 'PADD 5 - West Coast', 'value': 'PADD 5'},
                ],
                value='US',
                style={'width': '300px', 'display': 'inline-block'}
            )
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        html.Div([
            html.H3('Port Performance Summary', style={'marginBottom': '20px'}),
            html.Div(id='port-summary-table')
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div(id='port-volume-chart',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='port-efficiency-scatter',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='port-utilization-gauge',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='port-padd-distribution',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='port-quality-heatmap',
                    style={'width': '100%'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('port-summary-table', 'children'),
     Output('port-volume-chart', 'children'),
     Output('port-efficiency-scatter', 'children'),
     Output('port-utilization-gauge', 'children'),
     Output('port-padd-distribution', 'children'),
     Output('port-quality-heatmap', 'children')],
    Input('padd-filter-port', 'value')
)
def update_port_charts(padd_filter):
    return (
        generate_port_summary_table(padd_filter),
        create_port_volume_chart(padd_filter),
        create_port_efficiency_scatter(padd_filter),
        create_port_utilization_gauge(padd_filter),
        create_port_padd_distribution(padd_filter),
        create_port_quality_heatmap(padd_filter)
    )