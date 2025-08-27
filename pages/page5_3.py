import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format, Group, Sign, Symbol, Scheme
import plotly.graph_objects as go
import plotly.express as px
from src.cli.cli_data_processor import CLIDataProcessor
from datetime import datetime, timedelta

processor = CLIDataProcessor()

def generate_quality_distribution_table(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('P', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    quality_dist = filtered_processor.get_quality_distribution()
    
    quality_dist = quality_dist.reset_index()
    quality_dist.columns = ['Category', 'API Volume', 'Sulfur Volume', 'API %', 'Sulfur %']
    
    api_data = quality_dist[['Category', 'API Volume', 'API %']].dropna()
    sulfur_data = quality_dist[['Category', 'Sulfur Volume', 'Sulfur %']].dropna()
    
    combined_data = []
    for _, row in api_data.iterrows():
        combined_data.append({
            'Type': 'API',
            'Category': row['Category'],
            'Volume (kbd)': f"{row['API Volume']:,.0f}",
            'Percentage': f"{row['API %']:.1f}%"
        })
    
    for _, row in sulfur_data.iterrows():
        combined_data.append({
            'Type': 'Sulfur', 
            'Category': row['Category'],
            'Volume (kbd)': f"{row['Sulfur Volume']:,.0f}",
            'Percentage': f"{row['Sulfur %']:.1f}%"
        })
    
    return dash_table.DataTable(
        data=combined_data,
        columns=[
            {"name": "Type", "id": "Type"},
            {"name": "Category", "id": "Category"},
            {"name": "Volume (kbd)", "id": "Volume (kbd)"},
            {"name": "Percentage", "id": "Percentage"}
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'}
    )

def generate_arbitrage_table(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('P', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    arbitrage = filtered_processor.get_quality_arbitrage_opportunities()
    
    # Define custom formatting for each row based on metric type
    def get_format_for_metric(metric_name):
        if 'Volume' in metric_name:
            return Format(precision=1, group=Group.yes, group_delimiter=',')
        elif 'Ratio' in metric_name or 'Spread' in metric_name:
            return Format(precision=2)
        elif 'API' in metric_name:
            return Format(precision=1)
        elif 'Sulfur' in metric_name:
            return Format(precision=2)
        else:
            return Format(precision=2)
    
    return dash_table.DataTable(
        data=arbitrage.to_dict('records'),
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Value", "id": "Value", "type": "numeric", "format": Format(precision=2, group=Group.yes, group_delimiter=',')}
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'}
    )

def create_api_sulfur_scatter(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('P', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    df_recent = filtered_processor.get_date_filtered_data(
        start_date=datetime.now() - timedelta(days=365)
    )
    
    sample = df_recent.sample(min(5000, len(df_recent)))
    
    fig = go.Figure(go.Scatter(
        x=sample['APIGRAVITY'],
        y=sample['SULFUR'],
        mode='markers',
        marker=dict(
            size=sample['QUANTITY'] * 10,  # Scale up for visibility (kbd values are small)
            color=sample['QUANTITY'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Volume<br>(kbd)'),
            opacity=0.6,
            sizemode='area',
            sizemin=4  # Minimum marker size for visibility
        ),
        text=sample['CNTRY_NAME'],
        hovertemplate='<b>%{text}</b><br>API: %{x:.1f}<br>Sulfur: %{y:.2f}%<br>Volume: %{color:.1f} kbd<extra></extra>'
    ))
    
    fig.update_layout(
        title='Crude Quality Distribution (API vs Sulfur)',
        xaxis_title='API Gravity',
        yaxis_title='Sulfur Content (%)',
        template='plotly_white',
        height=500
    )
    
    return dcc.Graph(figure=fig)

def create_quality_evolution(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('P', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD').agg({
        'APIGRAVITY': 'mean',
        'SULFUR': 'mean'
    }).rolling(window=3, center=True).mean()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly['APIGRAVITY'],
        mode='lines',
        name='API Gravity',
        yaxis='y',
        line=dict(color='#2E86AB', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly['SULFUR'],
        mode='lines',
        name='Sulfur %',
        yaxis='y2',
        line=dict(color='#A23B72', width=2)
    ))
    
    fig.update_layout(
        title='Quality Evolution Over Time',
        xaxis_title='Date',
        yaxis=dict(title='API Gravity', side='left'),
        yaxis2=dict(title='Sulfur %', overlaying='y', side='right'),
        template='plotly_white',
        height=450
    )
    
    return dcc.Graph(figure=fig)

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Crude Quality Analysis',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-quality',
                options=[
                    {'label': 'US Total', 'value': 'US'},
                    {'label': 'PADD 1 (East Coast)', 'value': 'P1'},
                    {'label': 'PADD 2 (Midwest)', 'value': 'P2'},
                    {'label': 'PADD 3 (Gulf Coast)', 'value': 'P3'},
                    {'label': 'PADD 4 (Rocky Mountain)', 'value': 'P4'},
                    {'label': 'PADD 5 (West Coast)', 'value': 'P5'}
                ],
                value='US',
                style={'width': '300px'}
            )
        ], style={'marginBottom': '30px', 'textAlign': 'left'}),
        
        html.Div([
            html.Div([
                html.H3('Quality Distribution', style={'marginBottom': '20px'}),
                html.Div(id='quality-distribution-table')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.H3('Quality Arbitrage Metrics', style={'marginBottom': '20px'}),
                html.Div(id='arbitrage-table')
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right', 'verticalAlign': 'top'})
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div([html.Div(id='api-sulfur-scatter')],
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div([html.Div(id='quality-evolution-chart')],
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for updating charts and tables based on PADD filter
@callback(
    Output('quality-distribution-table', 'children'),
    Input('padd-filter-quality', 'value')
)
def update_quality_distribution_table(padd_filter):
    return generate_quality_distribution_table(padd_filter)

@callback(
    Output('arbitrage-table', 'children'),
    Input('padd-filter-quality', 'value')
)
def update_arbitrage_table(padd_filter):
    return generate_arbitrage_table(padd_filter)

@callback(
    Output('api-sulfur-scatter', 'children'),
    Input('padd-filter-quality', 'value')
)
def update_api_sulfur_scatter(padd_filter):
    return create_api_sulfur_scatter(padd_filter)

@callback(
    Output('quality-evolution-chart', 'children'),
    Input('padd-filter-quality', 'value')
)
def update_quality_evolution_chart(padd_filter):
    return create_quality_evolution(padd_filter)
