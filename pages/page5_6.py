import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format
import plotly.graph_objects as go
from src.cli.cli_data_processor import CLIDataProcessor
from app import app

processor = CLIDataProcessor()

def generate_seasonality_table(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    seasonality = filtered_processor.get_seasonality_analysis()
    
    return dash_table.DataTable(
        data=seasonality.to_dict('records'),
        columns=[
            {"name": "Month", "id": "Month Name"},
            {"name": "Avg Volume (Mbbl)", "id": "Avg Volume", "type": "numeric", "format": Format(precision=1)},
            {"name": "Seasonal Factor", "id": "Seasonal Factor", "type": "numeric", "format": Format(precision=1)},
            {"name": "Deviation %", "id": "Deviation from Mean", "type": "numeric", "format": Format(precision=1)}
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Deviation from Mean', 'filter_query': '{Deviation from Mean} > 5'},
                'backgroundColor': 'lightgreen',
                'color': 'green'
            },
            {
                'if': {'column_id': 'Deviation from Mean', 'filter_query': '{Deviation from Mean} < -5'},
                'backgroundColor': 'lightpink',
                'color': '#c00000'
            }
        ]
    )

def create_seasonal_decomposition(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    from statsmodels.tsa.seasonal import seasonal_decompose
    decomposition = seasonal_decompose(monthly, model='additive', period=12)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=decomposition.observed.index,
        y=decomposition.observed,
        mode='lines',
        name='Observed',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=decomposition.trend.index,
        y=decomposition.trend,
        mode='lines',
        name='Trend',
        line=dict(color='red', width=3)
    ))
    
    fig.update_layout(
        title='Import Volume Trend Analysis',
        xaxis_title='Date',
        yaxis_title='Volume (Thousand Barrels)',
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_monthly_pattern(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    seasonality = filtered_processor.get_seasonality_analysis()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=seasonality['Month Name'],
        y=seasonality['Deviation from Mean'],
        marker_color=np.where(seasonality['Deviation from Mean'] > 0, 'green', 'red'),
        text=seasonality['Deviation from Mean'].round(1),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Seasonal Pattern - Deviation from Annual Mean',
        xaxis_title='Month',
        yaxis_title='Deviation from Mean (%)',
        template='plotly_white',
        height=450
    )
    
    return dcc.Graph(figure=fig)

def create_forecast_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    from sklearn.linear_model import LinearRegression
    X = np.arange(len(monthly)).reshape(-1, 1)
    y = monthly.values
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_X = np.arange(len(monthly), len(monthly) + 6).reshape(-1, 1)
    forecast = model.predict(future_X)
    
    future_dates = pd.date_range(start=monthly.index[-1] + pd.DateOffset(months=1), periods=6, freq='MS')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines',
        name='Historical',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=forecast,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='6-Month Import Volume Forecast',
        xaxis_title='Date',
        yaxis_title='Volume (Thousand Barrels)',
        template='plotly_white',
        height=450
    )
    
    return dcc.Graph(figure=fig)

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Seasonal Patterns & Forecasting',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-seasonal',
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
            html.H3('Monthly Seasonality Index', style={'marginBottom': '20px'}),
            html.Div(id='seasonality-table')
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div(id='seasonal-decomposition',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='monthly-pattern-chart',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='forecast-chart')
        ], style={'marginBottom': '30px', 'width': '100%'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('seasonality-table', 'children'),
     Output('seasonal-decomposition', 'children'),
     Output('monthly-pattern-chart', 'children'),
     Output('forecast-chart', 'children')],
    Input('padd-filter-seasonal', 'value')
)
def update_seasonal_charts(padd_filter):
    return (
        generate_seasonality_table(padd_filter),
        create_seasonal_decomposition(padd_filter),
        create_monthly_pattern(padd_filter),
        create_forecast_chart(padd_filter)
    )
