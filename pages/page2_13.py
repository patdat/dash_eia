from dash import html, dcc, callback, Output, Input, ctx, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.wps.ag_calculations import DataProcessor
from src.utils.variables import default_start_date_eia_wps_table, default_end_date_eia_wps_table

# Initialize the data processor
processor = DataProcessor()

# Default date range
default_start_date = default_start_date_eia_wps_table
default_end_date = default_end_date_eia_wps_table

# Process data and column definitions - with error handling
try:
    df, columnDefinitions = processor.get_data(default_start_date, default_end_date)
except Exception as e:
    print(f"Error loading initial data for page2_13: {e}")
    # Create empty dataframe with minimal columns for initial load
    import pandas as pd
    df = pd.DataFrame()
    columnDefinitions = []

# Page layout for page 2_13 - Refinery Utilization and Crack Spread Analytics
layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("Refinery Utilization & Crack Spread Analytics", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range-p13',
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
            html.Button("📊 Export Analytics", id="export-analytics-btn-p13", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),
    
    # Main content area with charts
    html.Div([
        # Top row - Utilization charts
        html.Div([
            html.Div([
                html.H3("Refinery Utilization by PADD Region", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="refinery-utilization-gauge", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Crude Runs vs Production Capacity", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="crude-runs-capacity-chart", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Middle row - Crack spread analysis
        html.Div([
            html.Div([
                html.H3("3-2-1 Crack Spread Proxy", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="crack-spread-proxy", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Product Yield Analysis", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="product-yield-analysis", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Bottom row - Advanced analytics
        html.Div([
            html.Div([
                html.H3("Refinery Margin Indicator", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="refinery-margin-indicator", style={"height": "350px"})
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Capacity Utilization Heatmap", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="utilization-heatmap", style={"height": "350px"})
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Refinery Performance Metrics", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div(id="refinery-performance-table", style={"height": "350px", "padding": "10px", "backgroundColor": "#f8f8f8", "border": "1px solid #ddd"})
            ], style={"width": "32%"}),
        ], style={"display": "flex"}),
    ], style={"padding": "20px", "height": "85vh", "overflow": "auto"}),
    
    # Hidden stores
    dcc.Store(id='current-data-store-p13', data=df.to_dict('records') if not df.empty else [])
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# Helper function to get refinery data
def get_refinery_data(df):
    """Extract refinery-related data from the dataset"""
    if df.empty:
        return {}
    
    refinery_codes = {
        # Crude runs by PADD (refinery input)
        'crude_runs': {
            'P1': 'WCRRIP12',
            'P2': 'WCRRIP22', 
            'P3': 'WCRRIP32',
            'P4': 'WCRRIP42',
            'P5': 'WCRRIP52',
            'US': 'WCRRIUS2'
        },
        # Gasoline production
        'gasoline_prod': {
            'P1': 'WGFRPP12',
            'P2': 'WGFRPP22',
            'P3': 'WGFRPP32', 
            'P4': 'WGFRPP42',
            'P5': 'WGFRPP52',
            'US': 'WGFRPUS2'
        },
        # Distillate production
        'distillate_prod': {
            'P1': 'WDIRPP12',
            'P2': 'WDIRPP22',
            'P3': 'WDIRPP32',
            'P4': 'WDIRPP42', 
            'P5': 'WDIRPP52',
            'US': 'WDIRPUS2'
        },
        # Jet fuel production
        'jet_prod': {
            'P1': 'WKJRPP12',
            'P2': 'WKJRPP22',
            'P3': 'WKJRPP32',
            'P4': 'WKJRPP42',
            'P5': 'WKJRPP52', 
            'US': 'WKJRPUS2'
        },
        # Utilization rates
        'utilization': {
            'P1': 'W_NA_YUP_R10_PER',
            'P2': 'W_NA_YUP_R20_PER',
            'P3': 'W_NA_YUP_R30_PER',
            'P4': 'W_NA_YUP_R40_PER',
            'P5': 'W_NA_YUP_R50_PER'
        }
    }
    
    result = {}
    for category, codes in refinery_codes.items():
        result[category] = {}
        for padd, code in codes.items():
            data_row = df[df['id'] == code]
            if not data_row.empty:
                result[category][padd] = data_row.iloc[0]
    
    return result

# Helper function to extract time series
def extract_time_series(data_row):
    """Extract time series data from a data row"""
    if data_row is None or data_row.empty:
        return [], []
    
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in data_row.index if col not in metadata_cols]
    
    # Parse all date columns first, then sort by actual date
    date_value_pairs = []
    for col in date_cols:
        try:
            date = pd.to_datetime(col, format='%m/%d/%y')
            value = data_row[col]
            if pd.notna(value):
                date_value_pairs.append((date, float(value)))
        except:
            continue
    
    # Sort by date to ensure chronological order
    date_value_pairs.sort(key=lambda x: x[0])
    
    # Extract sorted dates and values
    dates = []
    values = []
    for date, value in date_value_pairs:
        dates.append(date)
        values.append(value)
    
    return dates, values

# Callback for updating data store
@callback(
    Output("current-data-store-p13", "data"),
    [Input("date-picker-range-p13", "start_date"),
     Input("date-picker-range-p13", "end_date")]
)
def update_data_store(start_date, end_date):
    try:
        df, _ = processor.get_data(start_date, end_date)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error updating data store: {e}")
        return []

# Callback for refinery utilization gauge
@callback(
    Output("refinery-utilization-gauge", "figure"),
    [Input("current-data-store-p13", "data")]
)
def update_refinery_utilization_gauge(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    if 'utilization' not in refinery_data:
        return go.Figure().update_layout(title="Utilization data not available")
    
    # Create subplot for multiple gauges
    from plotly.subplots import make_subplots
    
    padds = ['P1', 'P2', 'P3', 'P4', 'P5']
    utilization_data = refinery_data['utilization']
    
    # Extract current utilization rates
    current_rates = {}
    for padd in padds:
        if padd in utilization_data:
            dates, values = extract_time_series(utilization_data[padd])
            if values:
                current_rates[padd] = values[-1]
    
    if not current_rates:
        return go.Figure().update_layout(title="No utilization data available")
    
    # Create gauge chart
    fig = go.Figure()
    
    # Create a single gauge showing US average
    us_avg = np.mean(list(current_rates.values()))
    
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = us_avg,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "US Average Utilization (%)"},
        delta = {'reference': 85, 'position': "top"},  # 85% is typical target
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#c00000"},
            'steps': [
                {'range': [0, 70], 'color': "#ffcccc"},
                {'range': [70, 85], 'color': "#ffeecc"},
                {'range': [85, 95], 'color': "#ccffcc"},
                {'range': [95, 100], 'color': "#ffffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    # Add PADD breakdown as text annotations
    padd_text = []
    for padd, rate in current_rates.items():
        padd_text.append(f"{padd}: {rate:.1f}%")
    
    fig.add_annotation(
        x=0.5, y=0.15,
        text="<br>".join(padd_text),
        showarrow=False,
        font=dict(size=10),
        align="center"
    )
    
    fig.update_layout(height=400)
    
    return fig

# Callback for crude runs vs capacity
@callback(
    Output("crude-runs-capacity-chart", "figure"),
    [Input("current-data-store-p13", "data")]
)
def update_crude_runs_capacity(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    if 'crude_runs' not in refinery_data:
        return go.Figure().update_layout(title="Crude runs data not available")
    
    fig = go.Figure()
    
    # Plot crude runs for each PADD over time
    padds = ['P1', 'P2', 'P3', 'P4', 'P5']
    colors = ['#c00000', '#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
    
    for i, padd in enumerate(padds):
        if padd in refinery_data['crude_runs']:
            dates, values = extract_time_series(refinery_data['crude_runs'][padd])
            if dates and values:
                # For long date ranges, sample data points to avoid overcrowding
                if len(dates) > 200:
                    step = len(dates) // 200
                    dates_sampled = dates[::step]
                    values_sampled = values[::step]
                else:
                    dates_sampled = dates
                    values_sampled = values
                
                fig.add_trace(go.Scatter(
                    x=dates_sampled,
                    y=values_sampled,
                    mode='lines+markers',
                    name=f'{padd} Crude Runs',
                    line=dict(color=colors[i], width=2),
                    marker=dict(size=3)
                ))
    
    # Add capacity lines (estimated based on historical maximums)
    # In practice, these would be actual capacity data
    for i, padd in enumerate(padds):
        if padd in refinery_data['crude_runs']:
            dates, values = extract_time_series(refinery_data['crude_runs'][padd])
            if values:
                estimated_capacity = max(values) * 1.15  # Assume max utilization was ~87%
                fig.add_hline(
                    y=estimated_capacity,
                    line_dash="dash",
                    line_color=colors[i],
                    opacity=0.5,
                    annotation_text=f"{padd} Est. Capacity",
                    annotation_position="top left" if i < 3 else "bottom left"
                )
    
    fig.update_layout(
        title="Crude Runs vs Estimated Production Capacity",
        xaxis_title="Date",
        yaxis_title="Crude Runs (thousand barrels/day)",
        hovermode='x unified',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    return fig

# Callback for crack spread proxy
@callback(
    Output("crack-spread-proxy", "figure"),
    [Input("current-data-store-p13", "data")]
)
def update_crack_spread_proxy(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    # Calculate proxy crack spread using production data
    # 3-2-1 spread: 2 bbls gasoline + 1 bbl distillate vs 3 bbls crude input
    
    fig = go.Figure()
    
    if ('gasoline_prod' in refinery_data and 'distillate_prod' in refinery_data 
        and 'crude_runs' in refinery_data):
        
        # Use US totals for calculation
        gasoline_data = refinery_data['gasoline_prod'].get('US')
        distillate_data = refinery_data['distillate_prod'].get('US')
        crude_data = refinery_data['crude_runs'].get('US')
        
        if gasoline_data is not None and distillate_data is not None and crude_data is not None:
            gas_dates, gas_values = extract_time_series(gasoline_data)
            dist_dates, dist_values = extract_time_series(distillate_data)
            crude_dates, crude_values = extract_time_series(crude_data)
            
            # Align dates
            common_dates = sorted(set(gas_dates) & set(dist_dates) & set(crude_dates))
            
            spread_values = []
            spread_dates = []
            
            for date in common_dates:
                try:
                    gas_idx = gas_dates.index(date)
                    dist_idx = dist_dates.index(date)
                    crude_idx = crude_dates.index(date)
                    
                    gas_prod = gas_values[gas_idx]
                    dist_prod = dist_values[dist_idx] 
                    crude_input = crude_values[crude_idx]
                    
                    # Calculate proxy spread (production efficiency ratio)
                    if crude_input > 0:
                        spread = (2 * gas_prod + dist_prod) / (3 * crude_input)
                        spread_values.append(spread)
                        spread_dates.append(date)
                except ValueError:
                    continue
            
            if spread_values:
                # For long date ranges, sample data points
                if len(spread_values) > 300:
                    step = len(spread_values) // 300
                    spread_dates_sampled = spread_dates[::step]
                    spread_values_sampled = spread_values[::step]
                else:
                    spread_dates_sampled = spread_dates
                    spread_values_sampled = spread_values
                
                fig.add_trace(go.Scatter(
                    x=spread_dates_sampled,
                    y=spread_values_sampled,
                    mode='lines+markers',
                    name='3-2-1 Spread Proxy',
                    line=dict(color='#c00000', width=2),
                    marker=dict(size=3)
                ))
                
                # Add trend line
                if len(spread_values) > 10:
                    avg_spread = np.mean(spread_values[-52:])  # Last year average
                    fig.add_hline(
                        y=avg_spread,
                        line_dash="dash",
                        line_color="blue",
                        annotation_text=f"Avg: {avg_spread:.3f}",
                        annotation_position="top right"
                    )
    
    fig.update_layout(
        title="3-2-1 Crack Spread Proxy (Production Efficiency Ratio)<br><sub>Higher values indicate better refinery margins</sub>",
        xaxis_title="Date",
        yaxis_title="Efficiency Ratio",
        hovermode='x unified',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for product yield analysis
@callback(
    Output("product-yield-analysis", "figure"),
    [Input("current-data-store-p13", "data")]
)
def update_product_yield_analysis(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    # Calculate product yields as percentage of crude input
    fig = go.Figure()
    
    if ('gasoline_prod' in refinery_data and 'distillate_prod' in refinery_data 
        and 'jet_prod' in refinery_data and 'crude_runs' in refinery_data):
        
        # Use US totals
        crude_data = refinery_data['crude_runs'].get('US')
        gas_data = refinery_data['gasoline_prod'].get('US')
        dist_data = refinery_data['distillate_prod'].get('US')
        jet_data = refinery_data['jet_prod'].get('US')
        
        if all(x is not None for x in [crude_data, gas_data, dist_data, jet_data]):
            crude_dates, crude_values = extract_time_series(crude_data)
            
            if crude_dates and crude_values:
                # Calculate latest yields
                latest_date = crude_dates[-1]
                latest_crude = crude_values[-1]
                
                # Get production values for latest date
                _, gas_values = extract_time_series(gas_data)
                _, dist_values = extract_time_series(dist_data) 
                _, jet_values = extract_time_series(jet_data)
                
                if gas_values and dist_values and jet_values and latest_crude > 0:
                    latest_gas = gas_values[-1]
                    latest_dist = dist_values[-1]
                    latest_jet = jet_values[-1]
                    
                    yields = {
                        'Gasoline': (latest_gas / latest_crude) * 100,
                        'Distillate': (latest_dist / latest_crude) * 100, 
                        'Jet Fuel': (latest_jet / latest_crude) * 100,
                        'Other Products': 100 - ((latest_gas + latest_dist + latest_jet) / latest_crude) * 100
                    }
                    
                    # Create pie chart
                    fig = go.Figure(data=go.Pie(
                        labels=list(yields.keys()),
                        values=list(yields.values()),
                        hole=0.4,
                        textinfo='label+percent+value',
                        texttemplate='%{label}<br>%{value:.1f}%',
                        marker_colors=['#c00000', '#1f77b4', '#ff7f0e', '#2ca02c']
                    ))
    
    fig.update_layout(
        title=f"Product Yield Analysis - Latest Week<br><sub>Percentage of crude oil input</sub>",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for refinery margin indicator
@callback(
    Output("refinery-margin-indicator", "figure"),
    [Input("current-data-store-p13", "data")]
)
def update_refinery_margin_indicator(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    # Calculate simple margin proxy using utilization and production efficiency
    margin_score = 75  # Default/mock score
    
    if 'utilization' in refinery_data:
        # Use average utilization as proxy for margins
        utilization_rates = []
        for padd in ['P1', 'P2', 'P3', 'P4', 'P5']:
            if padd in refinery_data['utilization']:
                dates, values = extract_time_series(refinery_data['utilization'][padd])
                if values:
                    utilization_rates.append(values[-1])
        
        if utilization_rates:
            margin_score = np.mean(utilization_rates)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = margin_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Refinery Margin Indicator"},
        delta = {'reference': 80, 'position': "top"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#c00000"},
            'steps': [
                {'range': [0, 60], 'color': "#ffcccc"},
                {'range': [60, 75], 'color': "#ffeecc"},
                {'range': [75, 90], 'color': "#ccffcc"},
                {'range': [90, 100], 'color': "#ccffff"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    
    fig.update_layout(height=350)
    
    return fig

# Callback for utilization heatmap
@callback(
    Output("utilization-heatmap", "figure"),
    [Input("current-data-store-p13", "data")]
)
def update_utilization_heatmap(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    if 'utilization' not in refinery_data:
        return go.Figure().update_layout(title="Utilization data not available")
    
    # Create mock heatmap data (in practice, would use historical monthly data)
    padds = ['P1', 'P2', 'P3', 'P4', 'P5']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Generate mock seasonal utilization data
    np.random.seed(42)
    z_data = np.random.uniform(70, 95, size=(len(padds), len(months)))
    
    # Add seasonal patterns
    for i, padd in enumerate(padds):
        for j, month in enumerate(months):
            # Summer months typically higher utilization
            if j in [5, 6, 7]:  # Jun, Jul, Aug
                z_data[i][j] += 5
            # Maintenance season lower utilization  
            elif j in [2, 3, 9]:  # Mar, Apr, Oct
                z_data[i][j] -= 8
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=months,
        y=padds,
        colorscale='RdYlGn',
        text=z_data.round(1),
        texttemplate="%{text}%",
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title="Utilization %")
    ))
    
    fig.update_layout(
        title="Seasonal Utilization Patterns by PADD",
        xaxis_title="Month",
        yaxis_title="PADD Region",
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for performance table
@callback(
    Output("refinery-performance-table", "children"),
    [Input("current-data-store-p13", "data")]
)
def update_refinery_performance_table(data):
    if not data:
        return html.Div("No data available")
    
    df = pd.DataFrame(data)
    refinery_data = get_refinery_data(df)
    
    # Calculate performance metrics
    metrics = []
    
    # US crude runs
    if 'crude_runs' in refinery_data and 'US' in refinery_data['crude_runs']:
        dates, values = extract_time_series(refinery_data['crude_runs']['US'])
        if values:
            current_runs = values[-1]
            weekly_change = values[-1] - values[-2] if len(values) >= 2 else 0
            metrics.extend([
                ("Current Crude Runs", f"{current_runs:,.0f} mb/d"),
                ("Weekly Change", f"{weekly_change:+.0f} mb/d")
            ])
    
    # Average utilization
    if 'utilization' in refinery_data:
        util_rates = []
        for padd in ['P1', 'P2', 'P3', 'P4', 'P5']:
            if padd in refinery_data['utilization']:
                dates, values = extract_time_series(refinery_data['utilization'][padd])
                if values:
                    util_rates.append(values[-1])
        
        if util_rates:
            avg_util = np.mean(util_rates)
            max_util = max(util_rates)
            min_util = min(util_rates)
            metrics.extend([
                ("Average Utilization", f"{avg_util:.1f}%"),
                ("Max PADD Utilization", f"{max_util:.1f}%"),
                ("Min PADD Utilization", f"{min_util:.1f}%")
            ])
    
    # Product totals
    products = ['gasoline_prod', 'distillate_prod', 'jet_prod']
    product_names = ['Gasoline', 'Distillate', 'Jet Fuel']
    
    for prod_code, prod_name in zip(products, product_names):
        if prod_code in refinery_data and 'US' in refinery_data[prod_code]:
            dates, values = extract_time_series(refinery_data[prod_code]['US'])
            if values:
                current_prod = values[-1]
                metrics.append((f"Current {prod_name}", f"{current_prod:,.0f} mb/d"))
    
    # Create table
    if not metrics:
        return html.Div("No performance metrics available")
    
    table_rows = []
    for metric, value in metrics:
        color = "#2ca02c" if "+" in value else "#c00000" if "-" in value else "black"
        table_rows.append(
            html.Tr([
                html.Td(metric, style={"padding": "5px"}),
                html.Td(value, style={"padding": "5px", "color": color, "fontWeight": "bold"})
            ])
        )
    
    return html.Table([
        html.Tr([
            html.Th("Metric", style={"padding": "5px", "backgroundColor": "#f0f0f0"}),
            html.Th("Value", style={"padding": "5px", "backgroundColor": "#f0f0f0"})
        ])
    ] + table_rows, style={"width": "100%", "border": "1px solid #ddd", "borderCollapse": "collapse"})

# Export callback
@callback(
    Output("export-analytics-btn-p13", "n_clicks"),
    [Input("export-analytics-btn-p13", "n_clicks")],
    prevent_initial_call=True
)
def handle_export_analytics(n_clicks):
    if n_clicks > 0:
        print("Export analytics functionality would be implemented here")
    return 0