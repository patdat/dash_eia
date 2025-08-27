import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format, Group, Sign, Symbol
import plotly.graph_objects as go
import plotly.express as px
from src.cli.cli_data_processor import CLIDataProcessor
from datetime import datetime, timedelta
from app import app

processor = CLIDataProcessor()

def generate_market_summary_table(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    summary = filtered_processor.get_market_summary(period_months=1)
    
    data = [
        {'Metric': 'Total Import Volume (kbd)', 'Current': f"{summary['total_volume_current']:,.1f}", 
         'Previous': f"{summary['total_volume_previous']:,.1f}", 
         'Change %': f"{summary['volume_change_pct']:+.1f}%"},
        {'Metric': 'Active Importers', 'Current': summary['active_importers'], 
         'Previous': '-', 'Change %': '-'},
        {'Metric': 'Source Countries', 'Current': summary['source_countries'], 
         'Previous': '-', 'Change %': '-'},
        {'Metric': 'Avg API Gravity', 'Current': f"{summary['avg_api']:.1f}", 
         'Previous': '-', 'Change %': '-'},
        {'Metric': 'Avg Sulfur Content (%)', 'Current': f"{summary['avg_sulfur']:.2f}", 
         'Previous': '-', 'Change %': '-'},
        {'Metric': 'Top PADD', 'Current': f"PADD {int(summary['top_padd'])}", 
         'Previous': '-', 'Change %': '-'},
    ]
    
    return dash_table.DataTable(
        data=data,
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Current Month", "id": "Current"},
            {"name": "Previous Month", "id": "Previous"},
            {"name": "Change", "id": "Change %"}
        ],
        style_table={'border': 'none', 'borderRadius': '15px', 
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px', 
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black', 
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Change %', 'filter_query': '{Change %} contains "+"'},
                'backgroundColor': 'lightgreen',
                'color': 'green',
            },
            {
                'if': {'column_id': 'Change %', 'filter_query': '{Change %} contains "-"'},
                'backgroundColor': 'lightpink',
                'color': '#c00000',
            }
        ]
    )

def generate_disruption_alerts_table(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    alerts = filtered_processor.get_supply_disruption_alerts(threshold_pct=20)
    
    if alerts.empty:
        return html.Div("No significant supply disruptions detected", 
                       style={'padding': '20px', 'textAlign': 'center'})
    
    return dash_table.DataTable(
        data=alerts.to_dict('records'),
        columns=[
            {"name": "Country", "id": "Country"},
            {"name": "Change %", "id": "Change %", "type": "numeric", "format": Format(precision=1, sign=Sign.positive)},
            {"name": "Volume Impact (MB)", "id": "Volume Impact (MB)", "type": "numeric", "format": Format(precision=0, scheme=Scheme.fixed)},
            {"name": "Current kbd", "id": "Current kbd", "type": "numeric", "format": Format(precision=1)},
            {"name": "Affected Companies", "id": "Affected Companies"},
            {"name": "Signal", "id": "Signal"}
        ],
        style_table={'border': 'none', 'borderRadius': '15px', 
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px', 
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black', 
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Signal', 'filter_query': '{Signal} = "DISRUPTION"'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'Signal', 'filter_query': '{Signal} = "SURGE"'},
                'backgroundColor': '#c8e6c9',
                'color': '#1b5e20',
                'fontWeight': 'bold'
            }
        ]
    )

def create_volume_time_series(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    monthly_data = filtered_processor.get_monthly_trends(n_months=36)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_data.index,
        y=monthly_data['Volume'],
        mode='lines+markers',
        name='Monthly Volume',
        line=dict(color='#2E86AB', width=2),
        marker=dict(size=6)
    ))
    
    rolling_avg = monthly_data['Volume'].rolling(window=3, center=True).mean()
    fig.add_trace(go.Scatter(
        x=monthly_data.index,
        y=rolling_avg,
        mode='lines',
        name='3-Month Moving Avg',
        line=dict(color='#A23B72', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Crude Oil Import Volume Trend',
        xaxis_title='Date',
        yaxis_title='Volume (kbd)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return dcc.Graph(figure=fig)

def create_top_importers_chart(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    top_importers = filtered_processor.get_top_importers(n=10, period_months=1)
    
    fig = go.Figure(go.Bar(
        x=top_importers['Avg kbd'],
        y=top_importers.index,
        orientation='h',
        marker_color='#2E86AB',
        text=top_importers['Avg kbd'].apply(lambda x: f'{x:,.1f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Top 10 Importers (Current Month)',
        xaxis_title='Volume (kbd)',
        yaxis_title='Company',
        height=400,
        margin=dict(l=200),
        template='plotly_white'
    )
    
    return dcc.Graph(figure=fig)

def create_country_sources_chart(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    country_data = filtered_processor.get_country_analysis(n=10)
    
    fig = go.Figure(go.Pie(
        labels=country_data.index,
        values=country_data['Avg kbd'],
        hole=0.4,
        marker=dict(colors=px.colors.qualitative.Set3)
    ))
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Volume: %{value:,.1f} kbd<br>Share: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title='Import Sources by Country',
        height=400,
        showlegend=True,
        template='plotly_white'
    )
    
    return dcc.Graph(figure=fig)

def create_padd_distribution_chart():
    padd_data = processor.get_padd_summary()
    
    fig = go.Figure(go.Bar(
        x=padd_data.index,
        y=padd_data['Avg kbd'],
        marker_color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4B51'],
        text=padd_data['Avg kbd'].apply(lambda x: f'{x:,.1f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Import Distribution by PADD',
        xaxis_title='PADD Region',
        yaxis_title='Volume (kbd)',
        height=400,
        template='plotly_white'
    )
    
    return dcc.Graph(figure=fig)

def create_quality_heatmap(padd_filter='US'):
    # Filter data by PADD if specified
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    
    df_recent = filtered_processor.get_date_filtered_data(
        start_date=datetime.now() - timedelta(days=365)
    )
    
    country_quality = df_recent.groupby('CNTRY_NAME').agg({
        'APIGRAVITY': 'mean',
        'SULFUR': 'mean',
        'QUANTITY': 'sum'
    }).round(2)
    
    country_quality = country_quality.nlargest(15, 'QUANTITY')
    
    fig = go.Figure(go.Scatter(
        x=country_quality['APIGRAVITY'],
        y=country_quality['SULFUR'],
        mode='markers+text',
        marker=dict(
            size=country_quality['QUANTITY'] * 20,  # Scale up for visibility with kbd values
            color=country_quality['APIGRAVITY'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title='API Gravity'),
            line=dict(width=1, color='white'),
            sizemode='area',
            sizemin=10  # Minimum size for visibility
        ),
        text=country_quality.index,
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>API: %{x:.1f}<br>Sulfur: %{y:.2f}%<br><extra></extra>'
    ))
    
    fig.update_layout(
        title='Crude Quality by Country (Bubble Size = Volume)',
        xaxis_title='API Gravity',
        yaxis_title='Sulfur Content (%)',
        height=500,
        template='plotly_white',
        xaxis=dict(range=[15, 45]),
        yaxis=dict(range=[0, 4])
    )
    
    fig.add_shape(
        type='line',
        x0=31, x1=31, y0=0, y1=4,
        line=dict(color='gray', width=1, dash='dash')
    )
    fig.add_shape(
        type='line',
        x0=15, x1=45, y0=1, y1=1,
        line=dict(color='gray', width=1, dash='dash')
    )
    
    fig.add_annotation(x=38, y=0.5, text='Light Sweet', showarrow=False)
    fig.add_annotation(x=20, y=2.5, text='Heavy Sour', showarrow=False)
    
    return dcc.Graph(figure=fig)

def create_concentration_index_chart():
    monthly_hhi = []
    dates = pd.date_range(end=processor.df['RPT_PERIOD'].max(), periods=24, freq='MS')
    
    for date in dates:
        month_data = processor.df[processor.df['RPT_PERIOD'] == date]
        if not month_data.empty:
            shares = month_data.groupby('R_S_NAME')['QUANTITY'].sum()
            market_shares = (shares / shares.sum() * 100) ** 2
            hhi = market_shares.sum()
            monthly_hhi.append({'Date': date, 'HHI': hhi})
    
    hhi_df = pd.DataFrame(monthly_hhi)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hhi_df['Date'],
        y=hhi_df['HHI'],
        mode='lines+markers',
        name='Herfindahl Index',
        line=dict(color='#2E86AB', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_shape(
        type='line',
        x0=hhi_df['Date'].min(), x1=hhi_df['Date'].max(),
        y0=1500, y1=1500,
        line=dict(color='green', width=1, dash='dash')
    )
    fig.add_shape(
        type='line',
        x0=hhi_df['Date'].min(), x1=hhi_df['Date'].max(),
        y0=2500, y1=2500,
        line=dict(color='red', width=1, dash='dash')
    )
    
    fig.add_annotation(x=hhi_df['Date'].max(), y=1500, text='Low Concentration', 
                      showarrow=False, xanchor='right')
    fig.add_annotation(x=hhi_df['Date'].max(), y=2500, text='High Concentration', 
                      showarrow=False, xanchor='right')
    
    fig.update_layout(
        title='Market Concentration Trend (Herfindahl Index)',
        xaxis_title='Date',
        yaxis_title='HHI',
        height=400,
        template='plotly_white',
        yaxis=dict(range=[0, 3000])
    )
    
    return dcc.Graph(figure=fig)

layout = html.Div([
    html.Div([
        html.H1('EIA Company Level Imports - Market Overview', 
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-overview',
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
            html.Div([
                html.H3('Market Summary', style={'marginBottom': '20px'}),
                html.Div(id='market-summary-table')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.H3('Supply Disruption Alerts', style={'marginBottom': '20px'}),
                html.Div(id='disruption-alerts-table')
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right', 'verticalAlign': 'top'})
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div(id='volume-time-series', 
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='top-importers-chart', 
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='country-sources-chart', 
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='padd-distribution-chart', 
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='quality-heatmap', 
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='concentration-index-chart', 
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('market-summary-table', 'children'),
     Output('disruption-alerts-table', 'children'),
     Output('volume-time-series', 'children'),
     Output('top-importers-chart', 'children'),
     Output('country-sources-chart', 'children'),
     Output('padd-distribution-chart', 'children'),
     Output('quality-heatmap', 'children'),
     Output('concentration-index-chart', 'children')],
    Input('padd-filter-overview', 'value')
)
def update_overview_charts(padd_filter):
    return (
        generate_market_summary_table(padd_filter),
        generate_disruption_alerts_table(padd_filter),
        create_volume_time_series(padd_filter),
        create_top_importers_chart(padd_filter),
        create_country_sources_chart(padd_filter),
        create_padd_distribution_chart() if padd_filter == 'US' else create_padd_distribution_chart(),
        create_quality_heatmap(padd_filter),
        create_concentration_index_chart() if padd_filter == 'US' else create_concentration_index_chart()
    )