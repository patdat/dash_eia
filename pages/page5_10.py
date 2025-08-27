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

def generate_supply_disruption_alerts(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get disruption alerts with lower threshold for more sensitivity
    alerts = filtered_processor.get_supply_disruption_alerts(threshold_pct=10)
    
    # Add severity classification
    if not alerts.empty:
        def classify_severity(change):
            if abs(change) > 50:
                return 'CRITICAL'
            elif abs(change) > 25:
                return 'HIGH'
            elif abs(change) > 10:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        alerts['Severity'] = alerts['Change %'].apply(classify_severity)
        alerts['Days Since'] = (datetime.now() - pd.to_datetime('2024-01-01')).days  # Placeholder
    
    return dash_table.DataTable(
        data=alerts.to_dict('records') if not alerts.empty else [],
        columns=[
            {"name": "Country", "id": "Country"},
            {"name": "Change %", "id": "Change %", "type": "numeric", "format": Format(precision=1)},
            {"name": "Volume Impact (MB)", "id": "Volume Impact (MB)", "type": "numeric", "format": Format(precision=0, scheme=Scheme.fixed)},
            {"name": "Current kbd", "id": "Current kbd", "type": "numeric", "format": Format(precision=1)},
            {"name": "Signal", "id": "Signal"},
            {"name": "Severity", "id": "Severity"},
            {"name": "Affected Companies", "id": "Affected Companies"}
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
                'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "CRITICAL"'},
                'backgroundColor': '#b71c1c',
                'color': 'white'
            },
            {
                'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "HIGH"'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c'
            },
            {
                'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "MEDIUM"'},
                'backgroundColor': '#fff9c4',
                'color': '#f57c00'
            },
            {
                'if': {'column_id': 'Signal', 'filter_query': '{Signal} = "DISRUPTION"'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c'
            },
            {
                'if': {'column_id': 'Signal', 'filter_query': '{Signal} = "SURGE"'},
                'backgroundColor': '#c8e6c9',
                'color': '#1b5e20'
            }
        ]
    )

def create_alert_timeline(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate monthly volatility and identify alert periods
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    # Calculate rolling metrics
    pct_change = monthly.pct_change() * 100
    rolling_std = monthly.rolling(window=6).std()
    rolling_mean = monthly.rolling(window=6).mean()
    
    # Identify alert conditions
    volatility_threshold = rolling_std.quantile(0.8)
    volume_alerts = abs(pct_change) > 20
    volatility_alerts = rolling_std > volatility_threshold
    
    fig = go.Figure()
    
    # Monthly volumes
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines',
        name='Monthly Volume',
        line=dict(color='#2E86AB', width=2),
        yaxis='y'
    ))
    
    # Volume change percentage
    fig.add_trace(go.Scatter(
        x=pct_change.index,
        y=pct_change.values,
        mode='lines',
        name='Month-over-Month Change',
        line=dict(color='#A23B72', width=1),
        yaxis='y2'
    ))
    
    # Add alert markers
    alert_dates = monthly.index[volume_alerts | volatility_alerts]
    alert_volumes = monthly[volume_alerts | volatility_alerts]
    
    fig.add_trace(go.Scatter(
        x=alert_dates,
        y=alert_volumes,
        mode='markers',
        name='Alert Periods',
        marker=dict(
            color='red',
            size=10,
            symbol='triangle-up'
        ),
        yaxis='y'
    ))
    
    fig.update_layout(
        title='Market Alert Timeline',
        xaxis_title='Date',
        yaxis=dict(title='Volume (kbd)', side='left'),
        yaxis2=dict(title='Change %', overlaying='y', side='right'),
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_concentration_risk_gauge(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate various concentration metrics
    
    # Country concentration (HHI)
    country_shares = filtered_processor.df.groupby('CNTRY_NAME')['QUANTITY'].sum()
    country_hhi = ((country_shares / country_shares.sum() * 100) ** 2).sum()
    
    # Company concentration (HHI)
    company_shares = filtered_processor.df.groupby('R_S_NAME')['QUANTITY'].sum()
    company_hhi = ((company_shares / company_shares.sum() * 100) ** 2).sum()
    
    # Port concentration (HHI)
    port_shares = filtered_processor.df.groupby('PORT_CITY')['QUANTITY'].sum()
    port_hhi = ((port_shares / port_shares.sum() * 100) ** 2).sum()
    
    # Top 3 concentration (% of total volume)
    top3_countries = (country_shares.nlargest(3).sum() / country_shares.sum() * 100)
    
    fig = go.Figure()
    
    # Country HHI Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=country_hhi,
        domain={'x': [0, 0.48], 'y': [0.5, 1]},
        title={'text': "Country Concentration (HHI)"},
        delta={'reference': 1500, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 3000]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 1500], 'color': "lightgray"},
                {'range': [1500, 2500], 'color': "yellow"},
                {'range': [2500, 3000], 'color': "red"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 2500}
        }
    ))
    
    # Company HHI Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=company_hhi,
        domain={'x': [0.52, 1], 'y': [0.5, 1]},
        title={'text': "Company Concentration (HHI)"},
        delta={'reference': 1000, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 2500]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 1000], 'color': "lightgray"},
                {'range': [1000, 1800], 'color': "yellow"},
                {'range': [1800, 2500], 'color': "red"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1800}
        }
    ))
    
    # Top 3 Share Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=top3_countries,
        domain={'x': [0.2, 0.8], 'y': [0, 0.5]},
        title={'text': "Top 3 Countries Share (%)"},
        delta={'reference': 60, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkorange"},
            'steps': [
                {'range': [0, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "red"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 80}
        }
    ))
    
    fig.update_layout(
        title="Market Concentration Risk Dashboard",
        height=500
    )
    
    return dcc.Graph(figure=fig)

def create_anomaly_detection_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get monthly data and detect anomalies
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    # Calculate moving average and standard deviation
    window = 6
    moving_avg = monthly.rolling(window=window, center=True).mean()
    moving_std = monthly.rolling(window=window, center=True).std()
    
    # Define anomaly thresholds (2 standard deviations)
    upper_bound = moving_avg + 2 * moving_std
    lower_bound = moving_avg - 2 * moving_std
    
    # Identify anomalies
    anomalies_high = monthly > upper_bound
    anomalies_low = monthly < lower_bound
    
    fig = go.Figure()
    
    # Normal data
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines+markers',
        name='Monthly Volume',
        line=dict(color='#2E86AB', width=2),
        marker=dict(size=6)
    ))
    
    # Moving average
    fig.add_trace(go.Scatter(
        x=moving_avg.index,
        y=moving_avg.values,
        mode='lines',
        name='6-Month Moving Average',
        line=dict(color='gray', width=2, dash='dash')
    ))
    
    # Confidence bands
    fig.add_trace(go.Scatter(
        x=upper_bound.index,
        y=upper_bound.values,
        mode='lines',
        line=dict(color='lightgray', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=lower_bound.index,
        y=lower_bound.values,
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(128,128,128,0.2)',
        line=dict(color='lightgray', width=1),
        name='Normal Range (±2σ)',
        hoverinfo='skip'
    ))
    
    # High anomalies
    if anomalies_high.any():
        fig.add_trace(go.Scatter(
            x=monthly.index[anomalies_high],
            y=monthly.values[anomalies_high],
            mode='markers',
            name='High Anomalies',
            marker=dict(
                color='red',
                size=12,
                symbol='triangle-up'
            )
        ))
    
    # Low anomalies
    if anomalies_low.any():
        fig.add_trace(go.Scatter(
            x=monthly.index[anomalies_low],
            y=monthly.values[anomalies_low],
            mode='markers',
            name='Low Anomalies',
            marker=dict(
                color='orange',
                size=12,
                symbol='triangle-down'
            )
        ))
    
    fig.update_layout(
        title='Anomaly Detection in Import Volumes',
        xaxis_title='Date',
        yaxis_title='Volume (kbd)',
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_risk_heatmap(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate risk metrics by country
    countries = filtered_processor.df.groupby('CNTRY_NAME')['QUANTITY'].sum().nlargest(10).index
    
    risk_metrics = []
    for country in countries:
        country_data = filtered_processor.df[filtered_processor.df['CNTRY_NAME'] == country]
        
        # Volume volatility
        monthly_vol = country_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        volatility = (monthly_vol.std() / monthly_vol.mean() * 100) if len(monthly_vol) > 1 and monthly_vol.mean() > 0 else 0
        
        # Concentration risk (number of companies)
        company_count = country_data['R_S_NAME'].nunique()
        concentration = max(0, 100 - company_count * 10)  # Higher score for fewer companies
        
        # Port diversity
        port_count = country_data['PORT_CITY'].nunique()
        port_risk = max(0, 100 - port_count * 15)  # Higher score for fewer ports
        
        # Volume share risk
        total_volume = filtered_processor.df['QUANTITY'].sum()
        volume_share = (country_data['QUANTITY'].sum() / total_volume * 100)
        share_risk = min(100, volume_share * 2)  # Higher score for higher dependency
        
        risk_metrics.append([volatility, concentration, port_risk, share_risk])
    
    risk_categories = ['Volatility', 'Concentration', 'Port Diversity', 'Volume Share']
    
    fig = go.Figure(go.Heatmap(
        z=risk_metrics,
        x=risk_categories,
        y=[c[:15] for c in countries],
        colorscale='Reds',
        text=np.round(risk_metrics, 1),
        texttemplate='%{text:.1f}',
        textfont={"size": 10},
        colorbar=dict(title='Risk Score<br>(0-100)')
    ))
    
    fig.update_layout(
        title='Country Risk Assessment Matrix',
        xaxis_title='Risk Category',
        yaxis_title='Country',
        template='plotly_white',
        height=450
    )
    
    return dcc.Graph(figure=fig)

def generate_key_metrics_cards(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate key metrics
    total_volume = filtered_processor.df['QUANTITY'].sum()
    num_countries = filtered_processor.df['CNTRY_NAME'].nunique()
    num_companies = filtered_processor.df['R_S_NAME'].nunique()
    num_ports = filtered_processor.df['PORT_CITY'].nunique()
    
    # Calculate alerts count
    alerts = filtered_processor.get_supply_disruption_alerts(threshold_pct=10)
    active_alerts = len(alerts) if not alerts.empty else 0
    
    # Market concentration
    country_shares = filtered_processor.df.groupby('CNTRY_NAME')['QUANTITY'].sum()
    country_hhi = ((country_shares / country_shares.sum() * 100) ** 2).sum()
    concentration_level = 'High' if country_hhi > 2500 else 'Medium' if country_hhi > 1500 else 'Low'
    
    cards = [
        {
            'title': 'Total Volume',
            'value': f'{total_volume:,.0f} kbd',
            'color': '#2E86AB',
            'icon': '📊'
        },
        {
            'title': 'Active Alerts',
            'value': str(active_alerts),
            'color': '#e74c3c' if active_alerts > 5 else '#f39c12' if active_alerts > 0 else '#27ae60',
            'icon': '🚨'
        },
        {
            'title': 'Source Countries',
            'value': str(num_countries),
            'color': '#A23B72',
            'icon': '🌍'
        },
        {
            'title': 'Concentration Risk',
            'value': concentration_level,
            'color': '#e74c3c' if concentration_level == 'High' else '#f39c12' if concentration_level == 'Medium' else '#27ae60',
            'icon': '⚠️'
        }
    ]
    
    card_divs = []
    for card in cards:
        card_div = html.Div([
            html.Div([
                html.Span(card['icon'], style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Div([
                    html.H4(card['title'], style={'margin': '0', 'color': 'white'}),
                    html.H2(card['value'], style={'margin': '0', 'color': 'white'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={
            'backgroundColor': card['color'],
            'padding': '20px',
            'borderRadius': '10px',
            'margin': '10px',
            'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
            'width': '200px',
            'textAlign': 'center'
        })
        card_divs.append(card_div)
    
    return html.Div(card_divs, style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'})

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Market Alerts & Risk Dashboard',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-alerts',
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
        
        # Key Metrics Cards
        html.Div(id='key-metrics-cards', style={'marginBottom': '30px'}),
        
        html.Hr(),
        
        html.Div([
            html.H3('Active Supply Disruption Alerts', style={'marginBottom': '20px'}),
            html.Div(id='alerts-table')
        ], style={'marginBottom': '40px'}),
        
        html.Div([
            html.Div(id='alert-timeline-chart',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='anomaly-detection-chart',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='concentration-risk-gauge',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='risk-heatmap',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('key-metrics-cards', 'children'),
     Output('alerts-table', 'children'),
     Output('alert-timeline-chart', 'children'),
     Output('anomaly-detection-chart', 'children'),
     Output('concentration-risk-gauge', 'children'),
     Output('risk-heatmap', 'children')],
    Input('padd-filter-alerts', 'value')
)
def update_alerts_dashboard(padd_filter):
    return (
        generate_key_metrics_cards(padd_filter),
        generate_supply_disruption_alerts(padd_filter),
        create_alert_timeline(padd_filter),
        create_anomaly_detection_chart(padd_filter),
        create_concentration_risk_gauge(padd_filter),
        create_risk_heatmap(padd_filter)
    )