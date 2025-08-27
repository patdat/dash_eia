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

def create_sankey_diagram(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get top countries, companies, and PADDs
    top_countries = filtered_processor.df.groupby('CNTRY_NAME')['QUANTITY'].sum().nlargest(8).index
    top_companies = filtered_processor.df.groupby('R_S_NAME')['QUANTITY'].sum().nlargest(8).index
    top_padds = filtered_processor.df.groupby('PORT_PADD')['QUANTITY'].sum().nlargest(5).index
    
    # Create nodes
    nodes = []
    labels = []
    
    # Add country nodes
    for country in top_countries:
        nodes.append(country)
        labels.append(country[:15])
    
    # Add company nodes  
    for company in top_companies:
        nodes.append(company)
        labels.append(company[:20])
    
    # Add PADD nodes
    for padd in top_padds:
        nodes.append(f'PADD {padd}')
        labels.append(f'PADD {padd}')
    
    # Create links
    sources = []
    targets = []
    values = []
    
    # Country -> Company flows
    for i, country in enumerate(top_countries):
        country_data = filtered_processor.df[filtered_processor.df['CNTRY_NAME'] == country]
        for j, company in enumerate(top_companies):
            volume = country_data[country_data['R_S_NAME'] == company]['QUANTITY'].sum()
            if volume > 50:  # Only show significant flows
                sources.append(i)
                targets.append(len(top_countries) + j)
                values.append(volume)
    
    # Company -> PADD flows
    for j, company in enumerate(top_companies):
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        for k, padd in enumerate(top_padds):
            volume = company_data[company_data['PORT_PADD'] == padd]['QUANTITY'].sum()
            if volume > 50:  # Only show significant flows
                sources.append(len(top_countries) + j)
                targets.append(len(top_countries) + len(top_companies) + k)
                values.append(volume)
    
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["#2E86AB"] * len(top_countries) + ["#A23B72"] * len(top_companies) + ["#F18F01"] * len(top_padds)
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(128,128,128,0.5)"
        )
    ))
    
    fig.update_layout(
        title="Trade Flow Analysis (Country → Company → PADD)",
        font_size=10,
        height=600
    )
    
    return dcc.Graph(figure=fig)

def create_trade_matrix_heatmap(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Create company-country matrix
    matrix = filtered_processor.get_company_country_matrix(top_n=12)
    
    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=[c[:15] for c in matrix.columns],
        y=[r[:25] for r in matrix.index],
        colorscale='YlOrRd',
        text=matrix.values.round(1),
        texttemplate='%{text:.1f}%',
        textfont={"size": 9},
        colorbar=dict(title='% of Company<br>Total')
    ))
    
    fig.update_layout(
        title='Company-Country Dependency Matrix',
        xaxis_title='Country',
        yaxis_title='Company',
        template='plotly_white',
        height=500,
        xaxis_tickangle=-45,
        margin=dict(b=150)
    )
    
    return dcc.Graph(figure=fig)

def create_route_analysis_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Analyze country-PADD routes
    route_data = []
    for country in filtered_processor.df['CNTRY_NAME'].unique():
        country_data = filtered_processor.df[filtered_processor.df['CNTRY_NAME'] == country]
        total_volume = country_data['QUANTITY'].sum()
        
        for padd in country_data['PORT_PADD'].unique():
            padd_volume = country_data[country_data['PORT_PADD'] == padd]['QUANTITY'].sum()
            route_data.append({
                'Country': country,
                'PADD': f'PADD {padd}',
                'Volume': padd_volume,
                'Share': padd_volume / total_volume * 100,
                'Route': f'{country} → PADD {padd}'
            })
    
    route_df = pd.DataFrame(route_data)
    top_routes = route_df.nlargest(15, 'Volume')
    
    fig = go.Figure(go.Bar(
        x=top_routes['Volume'],
        y=top_routes['Route'],
        orientation='h',
        marker_color='#2E86AB',
        text=top_routes['Volume'].apply(lambda x: f'{x:.0f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Top 15 Trade Routes by Volume',
        xaxis_title='Volume (kbd)',
        yaxis_title='Route',
        height=500,
        margin=dict(l=200),
        template='plotly_white'
    )
    
    return dcc.Graph(figure=fig)

def create_diversification_analysis(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate diversification metrics
    diversification_data = []
    
    for padd in filtered_processor.df['PORT_PADD'].unique():
        padd_data = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd]
        
        # Country diversification (HHI)
        country_shares = padd_data.groupby('CNTRY_NAME')['QUANTITY'].sum()
        country_hhi = ((country_shares / country_shares.sum() * 100) ** 2).sum()
        
        # Company diversification
        company_shares = padd_data.groupby('R_S_NAME')['QUANTITY'].sum()
        company_hhi = ((company_shares / company_shares.sum() * 100) ** 2).sum()
        
        # Port diversification
        port_shares = padd_data.groupby('PORT_CITY')['QUANTITY'].sum()
        port_hhi = ((port_shares / port_shares.sum() * 100) ** 2).sum()
        
        diversification_data.append({
            'PADD': f'PADD {padd}',
            'Country HHI': country_hhi,
            'Company HHI': company_hhi,
            'Port HHI': port_hhi,
            'Countries': padd_data['CNTRY_NAME'].nunique(),
            'Companies': padd_data['R_S_NAME'].nunique(),
            'Ports': padd_data['PORT_CITY'].nunique()
        })
    
    div_df = pd.DataFrame(diversification_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=div_df['Countries'],
        y=div_df['Country HHI'],
        mode='markers+text',
        marker=dict(
            size=div_df['Companies'] * 2,
            color='#2E86AB',
            line=dict(width=2, color='white')
        ),
        text=div_df['PADD'],
        textposition='top center',
        name='Country Concentration',
        hovertemplate='<b>%{text}</b><br>Countries: %{x}<br>HHI: %{y:.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='PADD Diversification Analysis (Bubble Size = Companies)',
        xaxis_title='Number of Source Countries',
        yaxis_title='Country Concentration (HHI)',
        template='plotly_white',
        height=450,
        annotations=[
            dict(x=0.02, y=0.98, xref="paper", yref="paper",
                text="Lower HHI = More Diversified", showarrow=False,
                font=dict(size=12), bgcolor="rgba(255,255,255,0.8)")
        ]
    )
    
    return dcc.Graph(figure=fig)

def generate_trade_balance_table(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Calculate trade metrics by country
    country_stats = []
    countries = filtered_processor.df['CNTRY_NAME'].unique()[:15] if filtered_processor.df['CNTRY_NAME'].nunique() > 0 else []
    for country in countries:
        country_data = filtered_processor.df[filtered_processor.df['CNTRY_NAME'] == country]
        
        total_volume = country_data['QUANTITY'].sum()
        num_companies = country_data['R_S_NAME'].nunique()
        num_ports = country_data['PORT_CITY'].nunique()
        num_padds = country_data['PORT_PADD'].nunique()
        avg_api = country_data['APIGRAVITY'].mean()
        avg_sulfur = country_data['SULFUR'].mean()
        
        # Calculate stability (coefficient of variation)
        monthly_volumes = country_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        stability = (monthly_volumes.std() / monthly_volumes.mean() * 100) if len(monthly_volumes) > 1 else 0
        
        country_stats.append({
            'Country': country,
            'Volume (kbd)': round(total_volume, 1),
            'Companies': num_companies,
            'Ports': num_ports,
            'PADDs': num_padds,
            'Avg API': round(avg_api, 1),
            'Avg Sulfur %': round(avg_sulfur, 2),
            'Stability': round(stability, 1)
        })
    
    stats_df = pd.DataFrame(country_stats).sort_values('Volume (kbd)', ascending=False)
    
    return dash_table.DataTable(
        data=stats_df.to_dict('records'),
        columns=[
            {"name": "Country", "id": "Country"},
            {"name": "Volume (kbd)", "id": "Volume (kbd)", "type": "numeric", "format": Format(precision=1)},
            {"name": "Companies", "id": "Companies"},
            {"name": "Ports", "id": "Ports"},
            {"name": "PADDs", "id": "PADDs"},
            {"name": "Avg API", "id": "Avg API", "type": "numeric", "format": Format(precision=1)},
            {"name": "Avg Sulfur %", "id": "Avg Sulfur %", "type": "numeric", "format": Format(precision=2)},
            {"name": "Stability (CV%)", "id": "Stability", "type": "numeric", "format": Format(precision=1)}
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
                'if': {'column_id': 'Stability', 'filter_query': '{Stability} > 50'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c'
            },
            {
                'if': {'column_id': 'Stability', 'filter_query': '{Stability} < 20'},
                'backgroundColor': '#c8e6c9',
                'color': '#1b5e20'
            }
        ],
        page_size=15,
        sort_action='native'
    )

def create_flow_timeline_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    # Get top 5 countries
    top_countries = filtered_processor.df.groupby('CNTRY_NAME')['QUANTITY'].sum().nlargest(5).index
    
    fig = go.Figure()
    
    for country in top_countries:
        country_data = filtered_processor.df[filtered_processor.df['CNTRY_NAME'] == country]
        monthly = country_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly.values,
            mode='lines+markers',
            name=country,
            line=dict(width=2),
            marker=dict(size=6),
            stackgroup='one' if padd_filter != 'US' else None
        ))
    
    fig.update_layout(
        title='Trade Flow Timeline (Top 5 Countries)',
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

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Trade Flow & Route Analysis',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-trade-flow',
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
            html.H3('Country Trade Statistics', style={'marginBottom': '20px'}),
            html.Div(id='trade-balance-table')
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div(id='sankey-diagram',
                    style={'width': '100%'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='route-analysis-chart',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='diversification-analysis',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='trade-matrix-heatmap',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='flow-timeline-chart',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('trade-balance-table', 'children'),
     Output('sankey-diagram', 'children'),
     Output('route-analysis-chart', 'children'),
     Output('diversification-analysis', 'children'),
     Output('trade-matrix-heatmap', 'children'),
     Output('flow-timeline-chart', 'children')],
    Input('padd-filter-trade-flow', 'value')
)
def update_trade_flow_charts(padd_filter):
    return (
        generate_trade_balance_table(padd_filter),
        create_sankey_diagram(padd_filter),
        create_route_analysis_chart(padd_filter),
        create_diversification_analysis(padd_filter),
        create_trade_matrix_heatmap(padd_filter),
        create_flow_timeline_chart(padd_filter)
    )