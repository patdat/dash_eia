import pandas as pd
import numpy as np
from dash import html, dash_table, dcc
from dash.dash_table.Format import Format, Group, Sign, Symbol
import plotly.graph_objects as go
import plotly.express as px
from src.cli.cli_data_processor import CLIDataProcessor

processor = CLIDataProcessor()

def generate_padd_summary_table():
    padd_summary = processor.get_padd_summary()
    
    latest_date = processor.df['RPT_PERIOD'].max()
    prev_month = latest_date - pd.DateOffset(months=1)
    
    current = processor.df[processor.df['RPT_PERIOD'] == latest_date].groupby('PORT_PADD')['QUANTITY'].sum()
    previous = processor.df[processor.df['RPT_PERIOD'] == prev_month].groupby('PORT_PADD')['QUANTITY'].sum()
    
    padd_summary['MoM Change %'] = ((current - previous) / previous * 100).round(1)
    
    return dash_table.DataTable(
        data=padd_summary.reset_index().to_dict('records'),
        columns=[
            {"name": col, "id": col, "type": "numeric" if col != "index" else "text",
             "format": Format(precision=1, group=Group.yes, group_delimiter=',') if col == "Avg kbd" 
                      else Format(precision=1) if col not in ["index", "Companies", "Countries"] 
                      else Format(precision=0) if col in ["Companies", "Countries"]
                      else None}
            for col in padd_summary.reset_index().columns
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'MoM Change %', 'filter_query': '{MoM Change %} > 0'},
                'backgroundColor': 'lightgreen',
                'color': 'green'
            },
            {
                'if': {'column_id': 'MoM Change %', 'filter_query': '{MoM Change %} < 0'},
                'backgroundColor': 'lightpink',
                'color': '#c00000'
            }
        ]
    )

def generate_port_analysis_table():
    port_analysis = processor.get_port_analysis(n=15)
    
    return dash_table.DataTable(
        data=port_analysis.to_dict('records'),
        columns=[
            {"name": col, "id": col, "type": "numeric" if col not in ["Port", "PADD"] else "text",
             "format": Format(precision=1, group=Group.yes, group_delimiter=',') if col == "Total Volume"
                      else Format(precision=1) if col == "Market Share %"
                      else Format(precision=0) if col in ["Companies", "Countries", "PADD"]
                      else None}
            for col in port_analysis.columns
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
                    'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '11px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        page_size=15,
        sort_action="native"
    )

def create_padd_trends():
    padds = [1, 2, 3, 4, 5]
    
    fig = go.Figure()
    
    for padd in padds:
        padd_data = processor.df[processor.df['PORT_PADD'] == padd]
        monthly = padd_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly.values,
            mode='lines',
            name=f'PADD {padd}',
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title='PADD Import Trends',
        xaxis_title='Date',
        yaxis_title='Volume (Thousand Barrels)',
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_padd_source_mix():
    top_countries = processor.get_country_analysis(n=5).index
    
    padd_country = []
    for padd in range(1, 6):
        padd_data = processor.df[processor.df['PORT_PADD'] == padd]
        for country in top_countries:
            volume = padd_data[padd_data['CNTRY_NAME'] == country]['QUANTITY'].sum()
            padd_country.append({
                'PADD': f'PADD {padd}',
                'Country': country,
                'Volume': volume
            })
    
    df = pd.DataFrame(padd_country)
    
    fig = px.bar(df, x='PADD', y='Volume', color='Country',
                 title='Source Country Mix by PADD')
    
    fig.update_layout(
        xaxis_title='PADD Region',
        yaxis_title='Volume (Thousand Barrels)',
        template='plotly_white',
        height=450
    )
    
    return dcc.Graph(figure=fig)

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Regional/PADD Analysis',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        html.Div([
            html.H3('PADD Summary Statistics', style={'marginBottom': '20px'}),
            generate_padd_summary_table()
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.H3('Top Ports of Entry', style={'marginBottom': '20px'}),
            generate_port_analysis_table()
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div([create_padd_trends()],
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div([create_padd_source_mix()],
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])
