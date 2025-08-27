import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format
import plotly.graph_objects as go
import plotly.express as px
from src.cli.cli_data_processor import CLIDataProcessor
from app import app

processor = CLIDataProcessor()

def generate_country_risk_table(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    country_stats = filtered_processor.get_country_analysis(n=15)
    
    country_stats['Concentration'] = country_stats['Importers'].apply(
        lambda x: 'High Risk' if x < 3 else 'Medium Risk' if x < 6 else 'Low Risk'
    )
    
    return dash_table.DataTable(
        data=country_stats.reset_index().to_dict('records'),
        columns=[{"name": col, "id": col} for col in country_stats.reset_index().columns],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '11px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Concentration', 'filter_query': '{Concentration} = "High Risk"'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c'
            },
            {
                'if': {'column_id': 'Concentration', 'filter_query': '{Concentration} = "Medium Risk"'},
                'backgroundColor': '#fff9c4',
                'color': '#f57c00'
            },
            {
                'if': {'column_id': 'Concentration', 'filter_query': '{Concentration} = "Low Risk"'},
                'backgroundColor': '#c8e6c9',
                'color': '#1b5e20'
            }
        ],
        page_size=15,
        sort_action="native"
    )

def create_country_trends(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_countries = filtered_processor.get_country_analysis(n=10).index[:5]
    
    fig = go.Figure()
    
    for country in top_countries:
        country_data = filtered_processor.df[filtered_processor.df['CNTRY_NAME'] == country]
        monthly = country_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly.values,
            mode='lines',
            name=country,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title='Top 5 Countries Import Trends',
        xaxis_title='Date',
        yaxis_title='Volume (Thousand Barrels)',
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_geographic_distribution(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    country_data = filtered_processor.get_country_analysis(n=20)
    
    fig = go.Figure(go.Scattergeo(
        locations=['CAN', 'MEX', 'SAU', 'IRQ', 'COL', 'VEN', 'ECU', 'NGA', 'BRA', 'RUS'],
        locationmode='ISO-3',
        marker=dict(
            size=country_data['Avg kbd'].head(10) / 50,
            color=country_data['Avg API'].head(10),
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title='Avg API'),
            line=dict(width=1, color='white')
        ),
        text=country_data.index[:10],
        hovertemplate='<b>%{text}</b><br>Volume: %{marker.size:.0f}<br>API: %{marker.color:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Geographic Distribution of Imports',
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 245, 255)'
        ),
        height=500
    )
    
    return dcc.Graph(figure=fig)

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Country & Geopolitical Risk Analysis',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-country-risk',
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
            html.H3('Country Risk Assessment', style={'marginBottom': '20px'}),
            html.Div(id='country-risk-table')
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div(id='country-trends-chart',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='geographic-distribution',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('country-risk-table', 'children'),
     Output('country-trends-chart', 'children'),
     Output('geographic-distribution', 'children')],
    Input('padd-filter-country-risk', 'value')
)
def update_country_risk_charts(padd_filter):
    return (
        generate_country_risk_table(padd_filter),
        create_country_trends(padd_filter),
        create_geographic_distribution(padd_filter)
    )
