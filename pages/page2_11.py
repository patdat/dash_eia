from dash import html, dcc, callback, Output, Input, ctx, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.wps.ag_calculations import DataProcessor
from src.utils.variables import default_start_date_eia_wps_table, default_end_date_eia_wps_table

# Initialize the data processor
processor = DataProcessor()

# Dynamic date range - get most recent data
today = datetime.now()
# Start from 6 months ago for better visualization
default_start_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
default_end_date = today.strftime('%Y-%m-%d')

# Process data and column definitions - with error handling
try:
    df, columnDefinitions = processor.get_data(default_start_date, default_end_date)
except Exception as e:
    print(f"Error loading initial data for page2_11: {e}")
    # Create empty dataframe with minimal columns for initial load
    import pandas as pd
    df = pd.DataFrame()
    columnDefinitions = []

# Page layout for page 2_11 - PADD Regional Stock Comparison Charts
layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("PADD Regional Stock Analysis", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range-p11',
                min_date_allowed='2010-01-01',
                max_date_allowed='2030-12-31',
                initial_visible_month=default_start_date,
                start_date=default_start_date,
                end_date=default_end_date,
                display_format='YYYY-MM-DD',
                style={"padding": "10px"},
                className="custom-date-picker"
            ),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"}),

        html.Div([
            html.Button("📊 Export Data", id="export-data-btn-p11", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),
    
    # Main content area with charts
    html.Div([
        # Top row - Current Stock Levels by PADD
        html.Div([
            html.Div([
                html.H3("Current Stock Levels by PADD Region", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="padd-stocks-bar-chart", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Days of Supply by Product & PADD", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="days-supply-heatmap", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Middle row - Stock Changes Analysis
        html.Div([
            html.Div([
                html.H3("Weekly Stock Changes (Builds/Draws)", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="stock-changes-waterfall", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Regional Stock Distribution", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="regional-stock-pie", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Bottom row - Time Series Analysis
        html.Div([
            html.Div([
                html.H3("Stock Levels Over Time by PADD", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    html.Label("Select Product:", style={"marginRight": "10px"}),
                    dcc.Dropdown(
                        id='product-selector-p11',
                        options=[
                            {'label': 'Crude Oil', 'value': 'crude'},
                            {'label': 'Gasoline', 'value': 'gasoline'},
                            {'label': 'Distillate', 'value': 'distillate'},
                            {'label': 'Jet Fuel', 'value': 'jet'}
                        ],
                        value='crude',
                        style={"width": "200px", "display": "inline-block"}
                    )
                ], style={"margin": "10px 0"}),
                dcc.Graph(id="padd-time-series", style={"height": "350px"})
            ], style={"width": "100%"}),
        ], style={"display": "flex"}),
    ], style={"padding": "20px", "height": "85vh", "overflow": "auto"}),
    
    # Hidden stores
    dcc.Store(id='current-data-store-p11', data=df.to_dict('records') if not df.empty else [])
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# Helper function to get stock data by PADD and commodity
def get_stock_data_by_padd(df, commodity_type='crude'):
    """Extract stock data for specific commodity by PADD region"""
    if df.empty:
        return pd.DataFrame()
    
    # Define the mapping based on commodity type
    if commodity_type == 'crude':
        padd_mapping = {
            'P1': ['WCESTP11'],
            'P2': ['WCESTP21'], 
            'P3': ['WCESTP31'],
            'P4': ['WCESTP41'],
            'P5': ['WCESTP51'],
            'US': ['WCESTUS1'],
            'CUSHING': ['W_EPC0_SAX_YCUOK_MBBL']
        }
    elif commodity_type == 'gasoline':
        padd_mapping = {
            'P1': ['WGTSTP11'],
            'P2': ['WGTSTP21'],
            'P3': ['WGTSTP31'],
            'P4': ['WGTSTP41'],
            'P5': ['WGTSTP51'],
            'US': ['WGTSTUS1']
        }
    elif commodity_type == 'distillate':
        padd_mapping = {
            'P1': ['WDISTP11'],
            'P2': ['WDISTP21'],
            'P3': ['WDISTP31'],
            'P4': ['WDISTP41'],
            'P5': ['WDISTP51'],
            'US': ['WDISTUS1']
        }
    elif commodity_type == 'jet':
        padd_mapping = {
            'P1': ['WKJSTP11'],
            'P2': ['WKJSTP21'],
            'P3': ['WKJSTP31'],
            'P4': ['WKJSTP41'],
            'P5': ['WKJSTP51'],
            'US': ['WKJSTUS1']
        }
    else:
        return pd.DataFrame()
    
    result = []
    for padd, codes in padd_mapping.items():
        for code in codes:
            row_data = df[df['id'] == code]
            if not row_data.empty:
                result.append({
                    'padd': padd,
                    'code': code,
                    'name': row_data['name'].iloc[0],
                    'data': row_data
                })
    
    return pd.DataFrame(result)

# Callback for updating data store
@callback(
    Output("current-data-store-p11", "data"),
    [Input("date-picker-range-p11", "start_date"),
     Input("date-picker-range-p11", "end_date")]
)
def update_data_store(start_date, end_date):
    try:
        df, _ = processor.get_data(start_date, end_date)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error updating data store: {e}")
        return []

# Callback for PADD stocks bar chart
@callback(
    Output("padd-stocks-bar-chart", "figure"),
    [Input("current-data-store-p11", "data")]
)
def update_padd_stocks_bar(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    
    # Get latest date column
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in df.columns if col not in metadata_cols]
    if not date_cols:
        return go.Figure().update_layout(title="No date data available")
    
    latest_date = max(date_cols)
    
    fig = go.Figure()
    
    # Add bars for each product type
    commodities = ['crude', 'gasoline', 'distillate', 'jet']
    colors = ['#c00000', '#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, commodity in enumerate(commodities):
        stock_data = get_stock_data_by_padd(df, commodity)
        if not stock_data.empty:
            padds = []
            values = []
            
            for _, row in stock_data.iterrows():
                if row['padd'] != 'US' and row['padd'] != 'CUSHING':  # Exclude US total and Cushing
                    padd_data = row['data']
                    if latest_date in padd_data.columns:
                        value = padd_data[latest_date].iloc[0]
                        if pd.notna(value):
                            padds.append(row['padd'])
                            values.append(float(value))
            
            if padds and values:
                fig.add_trace(go.Bar(
                    name=commodity.title(),
                    x=padds,
                    y=values,
                    marker_color=colors[i],
                    text=[f"{val:,.0f}" for val in values],
                    textposition='outside'
                ))
    
    # Convert latest_date to datetime and format it properly
    try:
        date_obj = pd.to_datetime(latest_date, format='%m/%d/%y')
        formatted_date = date_obj.strftime('%Y-%m-%d')
    except:
        formatted_date = latest_date
    
    fig.update_layout(
        title=f"Current Stock Levels by PADD Region ({formatted_date})",
        xaxis_title="PADD Region",
        yaxis_title="Stock Level (thousand barrels)",
        barmode='group',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for days of supply heatmap
@callback(
    Output("days-supply-heatmap", "figure"),
    [Input("current-data-store-p11", "data")]
)
def update_days_supply_heatmap(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    
    # Calculate approximate days of supply (simplified calculation)
    # This would need actual consumption/demand data for accurate calculation
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in df.columns if col not in metadata_cols]
    
    if len(date_cols) < 2:
        return go.Figure().update_layout(title="Insufficient data for days of supply calculation")
    
    # Use last 4 weeks to estimate consumption rate
    recent_dates = sorted(date_cols)[-4:]
    
    commodities = ['Crude', 'Gasoline', 'Distillate', 'Jet Fuel']
    padds = ['P1', 'P2', 'P3', 'P4', 'P5']
    
    # Create mock days of supply data (in real implementation, calculate from actual consumption)
    np.random.seed(42)  # For consistent mock data
    z_data = np.random.randint(15, 45, size=(len(commodities), len(padds)))
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=padds,
        y=commodities,
        colorscale='RdYlGn',
        text=z_data,
        texttemplate="%{text} days",
        textfont={"size": 12},
        hoverongaps=False,
        colorbar=dict(title="Days of Supply")
    ))
    
    fig.update_layout(
        title="Days of Supply by Product & PADD Region",
        xaxis_title="PADD Region", 
        yaxis_title="Product",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for stock changes waterfall
@callback(
    Output("stock-changes-waterfall", "figure"),
    [Input("current-data-store-p11", "data")]
)
def update_stock_changes_waterfall(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    
    # Get last two weeks to calculate changes
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in df.columns if col not in metadata_cols]
    
    if len(date_cols) < 2:
        return go.Figure().update_layout(title="Insufficient data for change calculation")
    
    current_date = sorted(date_cols)[-1]
    previous_date = sorted(date_cols)[-2]
    
    # Calculate changes for crude oil by PADD
    stock_data = get_stock_data_by_padd(df, 'crude')
    
    changes = []
    labels = []
    
    if not stock_data.empty:
        for _, row in stock_data.iterrows():
            if row['padd'] not in ['US', 'CUSHING']:  # Exclude totals
                padd_data = row['data']
                if current_date in padd_data.columns and previous_date in padd_data.columns:
                    current = padd_data[current_date].iloc[0]
                    previous = padd_data[previous_date].iloc[0]
                    if pd.notna(current) and pd.notna(previous):
                        change = float(current) - float(previous)
                        changes.append(change)
                        labels.append(f"{row['padd']}")
    
    if not changes:
        return go.Figure().update_layout(title="No change data available")
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Stock Changes",
        orientation="v",
        measure=["relative"] * len(changes),
        x=labels,
        y=changes,
        text=[f"{change:+,.0f}" for change in changes],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2ca02c"}},
        decreasing={"marker": {"color": "#c00000"}}
    ))
    
    # Convert dates to datetime and format them properly
    try:
        prev_date_obj = pd.to_datetime(previous_date, format='%m/%d/%y')
        curr_date_obj = pd.to_datetime(current_date, format='%m/%d/%y')
        formatted_prev = prev_date_obj.strftime('%Y-%m-%d')
        formatted_curr = curr_date_obj.strftime('%Y-%m-%d')
    except:
        formatted_prev = previous_date
        formatted_curr = current_date
    
    fig.update_layout(
        title=f"Weekly Crude Oil Stock Changes by PADD<br>({formatted_prev} to {formatted_curr})",
        xaxis_title="PADD Region",
        yaxis_title="Change (thousand barrels)",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for regional stock pie chart
@callback(
    Output("regional-stock-pie", "figure"),
    [Input("current-data-store-p11", "data")]
)
def update_regional_stock_pie(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in df.columns if col not in metadata_cols]
    if not date_cols:
        return go.Figure().update_layout(title="No date data available")
    
    latest_date = max(date_cols)
    
    # Get crude oil stock data
    stock_data = get_stock_data_by_padd(df, 'crude')
    
    if stock_data.empty:
        return go.Figure().update_layout(title="No stock data available")
    
    labels = []
    values = []
    
    for _, row in stock_data.iterrows():
        if row['padd'] not in ['US']:  # Exclude US total
            padd_data = row['data']
            if latest_date in padd_data.columns:
                value = padd_data[latest_date].iloc[0]
                if pd.notna(value) and float(value) > 0:
                    labels.append(row['padd'])
                    values.append(float(value))
    
    if not labels:
        return go.Figure().update_layout(title="No valid stock data available")
    
    fig = go.Figure(data=go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:,.0f} kb<br>(%{percent})',
        marker_colors=['#c00000', '#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd', '#8c564b']
    ))
    
    # Convert latest_date to datetime and format it properly
    try:
        date_obj = pd.to_datetime(latest_date, format='%m/%d/%y')
        formatted_date = date_obj.strftime('%Y-%m-%d')
    except:
        formatted_date = latest_date
    
    fig.update_layout(
        title=f"Regional Crude Oil Stock Distribution ({formatted_date})",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for PADD time series
@callback(
    Output("padd-time-series", "figure"),
    [Input("current-data-store-p11", "data"),
     Input("product-selector-p11", "value")]
)
def update_padd_time_series(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    stock_data = get_stock_data_by_padd(df, selected_product)
    
    if stock_data.empty:
        return go.Figure().update_layout(title=f"No {selected_product} data available")
    
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in df.columns if col not in metadata_cols]
    
    if not date_cols:
        return go.Figure().update_layout(title="No time series data available")
    
    fig = go.Figure()
    colors = ['#c00000', '#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
    
    # Collect all data to check for outliers
    all_values = []
    chart_data = []
    
    for i, (_, row) in enumerate(stock_data.iterrows()):
        if row['padd'] not in ['US']:  # Exclude US total
            padd_data = row['data']
            
            dates = []
            values = []
            
            # padd_data is a DataFrame with one row, get that row
            if not padd_data.empty:
                data_row = padd_data.iloc[0]
                
                # Parse all date columns first, then sort by actual date
                date_value_pairs = []
                for col in date_cols:
                    try:
                        if col in data_row.index:
                            date = pd.to_datetime(col, format='%m/%d/%y')
                            value = data_row[col]
                            if pd.notna(value):
                                date_value_pairs.append((date, float(value)))
                    except:
                        continue
                
                # Sort by date to ensure chronological order
                date_value_pairs.sort(key=lambda x: x[0])
                
                # Extract sorted dates and values
                for date, value in date_value_pairs:
                    dates.append(date)
                    values.append(value)
                    all_values.append(value)
            
            if dates and values:
                chart_data.append({
                    'padd': row['padd'],
                    'dates': dates,
                    'values': values,
                    'color_idx': i
                })
    
    # Check if CUSHING data is causing scale issues
    if all_values:
        median_val = np.median(all_values)
        q75 = np.percentile(all_values, 75)
        
        # If CUSHING has values much higher than PADD regions, put it on secondary y-axis
        cushing_secondary = False
        for data_item in chart_data:
            if data_item['padd'] == 'CUSHING' and data_item['values']:
                avg_cushing = np.mean(data_item['values'])
                if avg_cushing > q75 * 3:  # CUSHING values are 3x higher than 75th percentile
                    cushing_secondary = True
                    break
    
    # Add traces
    for data_item in chart_data:
        dates = data_item['dates']
        values = data_item['values']
        padd = data_item['padd']
        
        # Don't sample - Plotly can handle the data and will auto-optimize
        dates_sampled = dates
        values_sampled = values
        
        # Use secondary y-axis for CUSHING if it's an outlier
        yaxis = 'y2' if (cushing_secondary and padd == 'CUSHING') else 'y'
        
        trace_kwargs = {
            'x': dates_sampled,
            'y': values_sampled,
            'mode': 'lines+markers',
            'name': padd,
            'line': dict(color=colors[data_item['color_idx'] % len(colors)], width=2),
            'marker': dict(size=3)
        }
        
        # Add yaxis parameter only if using secondary axis
        if yaxis == 'y2':
            trace_kwargs['yaxis'] = 'y2'
        
        fig.add_trace(go.Scatter(**trace_kwargs))
    
    # Setup layout with potentially dual y-axes
    layout_kwargs = {
        'title': f"{selected_product.title()} Stock Levels Over Time by PADD Region",
        'xaxis_title': "Date",
        'yaxis_title': "Stock Level (thousand barrels)",
        'hovermode': 'x unified',
        'height': 450,  # Increased height to accommodate legend
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'legend': dict(
            orientation="h", 
            yanchor="top", 
            y=-0.15, 
            xanchor="center", 
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)"
        )
    }
    
    # Add secondary y-axis if needed for CUSHING
    if cushing_secondary:
        layout_kwargs['yaxis2'] = dict(
            title="CUSHING Stock Level (thousand barrels)",
            overlaying='y',
            side='right',
            showgrid=False
        )
        layout_kwargs['yaxis'] = dict(title="PADD Stock Level (thousand barrels)")
    
    fig.update_layout(**layout_kwargs)
    
    return fig

# Export callback
@callback(
    Output("export-data-btn-p11", "n_clicks"),
    [Input("export-data-btn-p11", "n_clicks")],
    prevent_initial_call=True
)
def handle_export(n_clicks):
    if n_clicks > 0:
        # In a real implementation, this would trigger a download
        print("Export functionality would be implemented here")
    return 0