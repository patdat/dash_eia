import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format, Group, Sign, Symbol, Scheme
import plotly.graph_objects as go
import plotly.express as px
from src.cli.cli_data_processor import CLIDataProcessor
from datetime import datetime, timedelta
from app import app

processor = CLIDataProcessor()

def generate_top_importers_table(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_importers = filtered_processor.get_top_importers(n=20)
    
    latest_date = filtered_processor.df['RPT_PERIOD'].max()
    year_ago = latest_date - pd.DateOffset(years=1)
    
    current_year = filtered_processor.df[filtered_processor.df['RPT_PERIOD'] >= year_ago].groupby('R_S_NAME')['QUANTITY'].sum()
    previous_year = filtered_processor.df[
        (filtered_processor.df['RPT_PERIOD'] >= year_ago - pd.DateOffset(years=1)) &
        (filtered_processor.df['RPT_PERIOD'] < year_ago)
    ].groupby('R_S_NAME')['QUANTITY'].sum()
    
    top_importers['YoY Change %'] = ((current_year - previous_year) / previous_year * 100).fillna(0).round(1)
    
    dependency_index = []
    for company in top_importers.index:
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        country_shares = company_data.groupby('CNTRY_NAME')['QUANTITY'].sum()
        market_shares = (country_shares / country_shares.sum() * 100) ** 2
        hhi = market_shares.sum()
        dependency_index.append(round(hhi, 0))
    
    top_importers['Dependency Index'] = dependency_index
    
    top_country = []
    for company in top_importers.index:
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        primary = company_data.groupby('CNTRY_NAME')['QUANTITY'].sum().idxmax()
        top_country.append(primary)
    
    top_importers['Primary Source'] = top_country
    
    # Get the data in the right format
    data = top_importers.reset_index()
    
    # The reset_index creates a column with the index name (R_S_NAME)
    data.rename(columns={
        'R_S_NAME': 'Company',
        'Avg kbd': 'Volume (kbd)',
        'Source Countries': 'Sources'
    }, inplace=True)
    
    # Add the calculated columns
    data['YoY Change %'] = data['Company'].map(dict(zip(top_importers.index, top_importers['YoY Change %']))).fillna(0)
    data['Dependency Index'] = dependency_index
    data['Primary Source'] = top_country
    
    return dash_table.DataTable(
        data=data.to_dict('records'),
        columns=[
            {"name": "Company", "id": "Company"},
            {"name": "Volume (kbd)", "id": "Volume (kbd)", "type": "numeric", 
             "format": Format(precision=1)},
            {"name": "Sources", "id": "Sources"},
            {"name": "Primary Source", "id": "Primary Source"},
            {"name": "Avg API", "id": "Avg API", "type": "numeric", 
             "format": Format(precision=1)},
            {"name": "Avg Sulfur %", "id": "Avg Sulfur", "type": "numeric", 
             "format": Format(precision=2)},
            {"name": "Market Share %", "id": "Market Share %", "type": "numeric", 
             "format": Format(precision=1)},
            {"name": "YoY Change %", "id": "YoY Change %", "type": "numeric", 
             "format": Format(precision=1, sign=Sign.positive)},
            {"name": "Dependency Index", "id": "Dependency Index", "type": "numeric"}
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
                'if': {'column_id': 'YoY Change %', 'filter_query': '{YoY Change %} > 0'},
                'backgroundColor': 'lightgreen',
                'color': 'green',
            },
            {
                'if': {'column_id': 'YoY Change %', 'filter_query': '{YoY Change %} < 0'},
                'backgroundColor': 'lightpink',
                'color': '#c00000',
            },
            {
                'if': {'column_id': 'Dependency Index', 'filter_query': '{Dependency Index} > 5000'},
                'backgroundColor': '#ffcdd2',
                'color': '#b71c1c',
            }
        ],
        page_size=20,
        sort_action='native',
        filter_action='native'
    )

def generate_dependency_matrix(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    matrix = filtered_processor.get_company_country_matrix(top_n=10)
    
    formatted_matrix = matrix.copy()
    for col in formatted_matrix.columns:
        formatted_matrix[col] = formatted_matrix[col].apply(lambda x: f'{x:.1f}%' if x > 0 else '-')
    
    formatted_matrix.reset_index(inplace=True)
    formatted_matrix.rename(columns={'index': 'Company'}, inplace=True)
    
    return dash_table.DataTable(
        data=formatted_matrix.to_dict('records'),
        columns=[{"name": col, "id": col} for col in formatted_matrix.columns],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
                    'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '8px',
                   'fontFamily': 'Arial', 'fontSize': '11px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Company'},
                'textAlign': 'left',
                'fontWeight': 'bold'
            }
        ]
    )

def create_company_trends_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_5_companies = filtered_processor.get_top_importers(n=5).index
    
    fig = go.Figure()
    
    for company in top_5_companies:
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        monthly = company_data.groupby('RPT_PERIOD')['QUANTITY'].sum()
        
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly.values,
            mode='lines+markers',
            name=company[:30],
            line=dict(width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title='Top 5 Companies Import Trends',
        xaxis_title='Date',
        yaxis_title='Volume (kbd)',
        hovermode='x unified',
        template='plotly_white',
        height=450,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )
    
    return dcc.Graph(figure=fig)

def create_market_share_evolution(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_7 = filtered_processor.get_top_importers(n=7)
    
    dates = pd.date_range(end=filtered_processor.df['RPT_PERIOD'].max(), periods=24, freq='MS')
    
    shares_data = []
    for date in dates:
        month_data = filtered_processor.df[filtered_processor.df['RPT_PERIOD'] == date]
        if not month_data.empty:
            total = month_data['QUANTITY'].sum()
            for company in top_7.index:
                company_volume = month_data[month_data['R_S_NAME'] == company]['QUANTITY'].sum()
                shares_data.append({
                    'Date': date,
                    'Company': company[:30],
                    'Market Share': (company_volume / total * 100) if total > 0 else 0
                })
    
    shares_df = pd.DataFrame(shares_data)
    
    fig = go.Figure()
    
    for company in shares_df['Company'].unique():
        company_data = shares_df[shares_df['Company'] == company]
        fig.add_trace(go.Scatter(
            x=company_data['Date'],
            y=company_data['Market Share'],
            mode='lines',
            name=company,
            stackgroup='one',
            line=dict(width=0.5)
        ))
    
    fig.update_layout(
        title='Market Share Evolution (Top 7 Companies)',
        xaxis_title='Date',
        yaxis_title='Market Share (%)',
        hovermode='x unified',
        template='plotly_white',
        height=450,
        showlegend=True
    )
    
    return dcc.Graph(figure=fig)

def create_dependency_scatter(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    company_stats = []
    for company in filtered_processor.df['R_S_NAME'].unique():
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        volume = company_data['QUANTITY'].sum()
        sources = company_data['CNTRY_NAME'].nunique()
        
        country_shares = company_data.groupby('CNTRY_NAME')['QUANTITY'].sum()
        market_shares = (country_shares / country_shares.sum() * 100) ** 2
        hhi = market_shares.sum()
        
        company_stats.append({
            'Company': company,
            'Volume': volume,
            'Sources': sources,
            'HHI': hhi,
            'Market Share': volume
        })
    
    stats_df = pd.DataFrame(company_stats)
    stats_df = stats_df[stats_df['Volume'] > 10]
    stats_df['Market Share'] = (stats_df['Market Share'] / stats_df['Market Share'].sum() * 100)
    
    fig = go.Figure(go.Scatter(
        x=stats_df['Volume'],
        y=stats_df['Sources'],
        mode='markers',
        marker=dict(
            size=stats_df['Market Share'] * 3,
            color=stats_df['HHI'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title='Concentration<br>Index'),
            line=dict(width=1, color='white')
        ),
        text=stats_df['Company'],
        hovertemplate='<b>%{text}</b><br>Volume: %{x:.0f} kbd<br>Sources: %{y}<br><extra></extra>'
    ))
    
    fig.update_layout(
        title='Company Dependency Analysis (Bubble Size = Market Share)',
        xaxis_title='Total Volume (kbd)',
        yaxis_title='Number of Source Countries',
        template='plotly_white',
        height=450,
        xaxis_type='log'
    )
    
    return dcc.Graph(figure=fig)

def create_quality_profile_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_10 = filtered_processor.get_top_importers(n=10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='API Gravity',
        x=top_10.index,
        y=top_10['Avg API'],
        marker_color='#2E86AB',
        yaxis='y',
        text=top_10['Avg API'].apply(lambda x: f'{x:.1f}'),
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Sulfur %',
        x=top_10.index,
        y=top_10['Avg Sulfur'],
        marker_color='#A23B72',
        yaxis='y2',
        text=top_10['Avg Sulfur'].apply(lambda x: f'{x:.1f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Crude Quality Profile by Company',
        xaxis=dict(title='Company', tickangle=-45),
        yaxis=dict(title='API Gravity', side='left'),
        yaxis2=dict(title='Sulfur %', overlaying='y', side='right'),
        template='plotly_white',
        height=450,
        margin=dict(b=150),
        barmode='group'
    )
    
    return dcc.Graph(figure=fig)

def create_monthly_pattern_heatmap(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_companies = filtered_processor.get_top_importers(n=12).index
    
    heatmap_data = []
    for company in top_companies:
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        monthly_avg = company_data.groupby(company_data['RPT_PERIOD'].dt.month)['QUANTITY'].mean()
        # Ensure we have all 12 months, fill missing with 0
        monthly_values = []
        for month in range(1, 13):
            if month in monthly_avg.index:
                monthly_values.append(monthly_avg[month])
            else:
                monthly_values.append(0)
        heatmap_data.append(monthly_values)
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Convert to numpy array for consistent shape
    heatmap_array = np.array(heatmap_data)
    
    fig = go.Figure(go.Heatmap(
        z=heatmap_array,
        x=months,
        y=[c[:25] for c in top_companies],
        colorscale='YlOrRd',
        text=np.round(heatmap_array, 1),
        texttemplate='%{text:.1f}',
        textfont={"size": 10},
        colorbar=dict(title='Avg kbd')
    ))
    
    fig.update_layout(
        title='Monthly Import Patterns by Company',
        xaxis_title='Month',
        yaxis_title='Company',
        template='plotly_white',
        height=500
    )
    
    return dcc.Graph(figure=fig)

def create_padd_distribution_chart(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    top_companies = filtered_processor.get_top_importers(n=8).index
    
    padd_dist = []
    for company in top_companies:
        company_data = filtered_processor.df[filtered_processor.df['R_S_NAME'] == company]
        padd_volumes = company_data.groupby('PORT_PADD')['QUANTITY'].sum()
        padd_pct = (padd_volumes / padd_volumes.sum() * 100).to_dict()
        
        for padd in range(1, 7):
            padd_dist.append({
                'Company': company[:25],
                'PADD': f'PADD {padd}',
                'Percentage': padd_pct.get(padd, 0)
            })
    
    dist_df = pd.DataFrame(padd_dist)
    
    fig = px.bar(dist_df, x='Company', y='Percentage', color='PADD',
                 color_discrete_map={
                     'PADD 1': '#2E86AB',
                     'PADD 2': '#A23B72', 
                     'PADD 3': '#F18F01',
                     'PADD 4': '#C73E1D',
                     'PADD 5': '#6A994E',
                     'PADD 6': '#BC4B51'
                 })
    
    fig.update_layout(
        title='PADD Distribution by Company',
        xaxis_title='Company',
        yaxis_title='Percentage of Imports',
        template='plotly_white',
        height=450,
        xaxis_tickangle=-45,
        margin=dict(b=150),
        barmode='stack'
    )
    
    return dcc.Graph(figure=fig)

def get_layout():
    return html.Div([
        html.Div([
            html.H1('EIA Company Level Imports - Company Analysis', 
                    style={'textAlign': 'center', 'marginBottom': '30px'}),
            
            # PADD Filter Dropdown
            html.Div([
                html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='padd-filter-company',
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
                html.H3('Top 20 Importers - Detailed Analysis', style={'marginBottom': '20px'}),
                html.Div(id='top-importers-table')
            ], style={'marginBottom': '40px'}),
            
            html.Hr(),
            
            html.Div([
                html.H3('Company-Country Dependency Matrix (% of Company Imports)', 
                       style={'marginBottom': '20px'}),
                html.Div(id='dependency-matrix')
            ], style={'marginBottom': '40px'}),
            
            html.Hr(),
            
            html.Div([
                html.Div(id='company-trends-chart', 
                        style={'width': '48%', 'display': 'inline-block'}),
                html.Div(id='market-share-evolution', 
                        style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
            ], style={'marginBottom': '30px'}),
            
            html.Div([
                html.Div(id='dependency-scatter', 
                        style={'width': '48%', 'display': 'inline-block'}),
                html.Div(id='quality-profile-chart', 
                        style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
            ], style={'marginBottom': '30px'}),
            
            html.Div([
                html.Div(id='monthly-pattern-heatmap', 
                        style={'width': '48%', 'display': 'inline-block'}),
                html.Div(id='padd-distribution-company', 
                        style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
            ], style={'marginBottom': '30px'})
            
        ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
    ])

# Create layout - will be called when page is accessed
layout = get_layout

# Callbacks for PADD filtering
@callback(
    [Output('top-importers-table', 'children'),
     Output('dependency-matrix', 'children'),
     Output('company-trends-chart', 'children'),
     Output('market-share-evolution', 'children'),
     Output('dependency-scatter', 'children'),
     Output('quality-profile-chart', 'children'),
     Output('monthly-pattern-heatmap', 'children'),
     Output('padd-distribution-company', 'children')],
    Input('padd-filter-company', 'value')
)
def update_company_charts(padd_filter):
    return (
        generate_top_importers_table(padd_filter),
        generate_dependency_matrix(padd_filter),
        create_company_trends_chart(padd_filter),
        create_market_share_evolution(padd_filter),
        create_dependency_scatter(padd_filter),
        create_quality_profile_chart(padd_filter),
        create_monthly_pattern_heatmap(padd_filter),
        create_padd_distribution_chart(padd_filter)
    )