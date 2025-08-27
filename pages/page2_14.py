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
    print(f"Error loading initial data for page2_14: {e}")
    # Create empty dataframe with minimal columns for initial load
    import pandas as pd
    df = pd.DataFrame()
    columnDefinitions = []

# Page layout for page 2_14 - Supply/Demand Balance & Import/Export Analysis
layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("Supply/Demand Balance & Trade Analysis", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range-p14',
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
            html.Button("📊 Export Balance Sheet", id="export-balance-btn-p14", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),
    
    # Main content area with charts
    html.Div([
        # Top row - Supply/Demand Overview
        html.Div([
            html.Div([
                html.H3("Crude Oil Supply/Demand Balance", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="supply-demand-waterfall", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Import Dependency by Product", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="import-dependency-chart", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Middle row - Trade flow analysis
        html.Div([
            html.Div([
                html.H3("Regional Import/Export Flows", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="trade-flow-sankey", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Net Imports vs Production", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="net-imports-vs-production", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Bottom row - Advanced analytics
        html.Div([
            html.Div([
                html.H3("Supply Security Index", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="supply-security-gauge", style={"height": "350px"})
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Product Balance Calendar", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    dcc.Dropdown(
                        id='product-balance-selector',
                        options=[
                            {'label': 'Crude Oil', 'value': 'crude'},
                            {'label': 'Gasoline', 'value': 'gasoline'},
                            {'label': 'Distillate', 'value': 'distillate'}
                        ],
                        value='crude',
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="product-balance-calendar", style={"height": "300px"})
                ])
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Trade Statistics", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div(id="trade-statistics-table", style={"height": "350px", "padding": "10px", "backgroundColor": "#f8f8f8", "border": "1px solid #ddd"})
            ], style={"width": "32%"}),
        ], style={"display": "flex"}),
    ], style={"padding": "20px", "height": "85vh", "overflow": "auto"}),
    
    # Hidden stores
    dcc.Store(id='current-data-store-p14', data=df.to_dict('records') if not df.empty else [])
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# Helper function to get supply/demand data
def get_supply_demand_data(df):
    """Extract supply/demand related data from the dataset"""
    if df.empty:
        return {}
    
    supply_demand_codes = {
        # Production/Supply
        'crude_production': 'WCRFPUS2',  # Field production
        'crude_runs': 'WCRRIUS2',  # Refinery inputs
        'crude_imports': 'WCEIMUS2',  # Imports
        'crude_exports': 'WCREXUS2',  # Exports
        'crude_stocks': 'WCESTUS1',  # Commercial stocks
        
        # Gasoline
        'gasoline_production': 'WGFRPUS2',
        'gasoline_imports': 'WGTIMUS2',
        'gasoline_stocks': 'WGTSTUS1',
        
        # Distillate  
        'distillate_production': 'WDIRPUS2',
        'distillate_imports': 'WDIIMUS2',
        'distillate_exports': 'WDIEXUS2',
        'distillate_stocks': 'WDISTUS1',
        
        # Jet fuel
        'jet_production': 'WKJRPUS2',
        'jet_imports': 'WKJIMUS2',
        'jet_exports': 'WKJEXUS2',
        'jet_stocks': 'WKJSTUS1',
        
        # Regional imports by PADD
        'crude_imports_p1': 'WCEIMP12',
        'crude_imports_p2': 'WCEIMP22', 
        'crude_imports_p3': 'WCEIMP32',
        'crude_imports_p4': 'WCEIMP42',
        'crude_imports_p5': 'WCEIMP52',
    }
    
    result = {}
    for category, code in supply_demand_codes.items():
        data_row = df[df['id'] == code]
        if not data_row.empty:
            result[category] = data_row.iloc[0]
    
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
    Output("current-data-store-p14", "data"),
    [Input("date-picker-range-p14", "start_date"),
     Input("date-picker-range-p14", "end_date")]
)
def update_data_store(start_date, end_date):
    try:
        df, _ = processor.get_data(start_date, end_date)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error updating data store: {e}")
        return []

# Callback for supply/demand waterfall
@callback(
    Output("supply-demand-waterfall", "figure"),
    [Input("current-data-store-p14", "data")]
)
def update_supply_demand_waterfall(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    # Get latest values for waterfall components
    components = ['crude_production', 'crude_imports', 'crude_exports', 'crude_runs']
    component_names = ['Production', 'Imports', 'Exports', 'Refinery Runs']
    values = []
    
    for component in components:
        if component in sd_data:
            dates, vals = extract_time_series(sd_data[component])
            if vals:
                latest_val = vals[-1]
                # Make exports negative for waterfall
                if component == 'crude_exports':
                    latest_val = -latest_val
                elif component == 'crude_runs':
                    latest_val = -latest_val  # Refinery consumption
                values.append(latest_val)
            else:
                values.append(0)
        else:
            values.append(0)
    
    if not any(values):
        return go.Figure().update_layout(title="No supply/demand data available")
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Supply/Demand Balance",
        orientation="v",
        measure=["relative", "relative", "relative", "relative"],
        x=component_names,
        y=values,
        text=[f"{val:+,.0f}" for val in values],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2ca02c"}},
        decreasing={"marker": {"color": "#c00000"}}
    ))
    
    fig.update_layout(
        title="Crude Oil Supply/Demand Balance (Latest Week)<br><sub>Thousand barrels per day</sub>",
        xaxis_title="Supply/Demand Components",
        yaxis_title="Volume (thousand barrels/day)",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for import dependency chart
@callback(
    Output("import-dependency-chart", "figure"),
    [Input("current-data-store-p14", "data")]
)
def update_import_dependency_chart(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    # Calculate import dependency for different products
    products = {
        'Crude Oil': {'imports': 'crude_imports', 'production': 'crude_production'},
        'Gasoline': {'imports': 'gasoline_imports', 'production': 'gasoline_production'},
        'Distillate': {'imports': 'distillate_imports', 'production': 'distillate_production'}
    }
    
    product_names = []
    dependency_ratios = []
    
    for product, codes in products.items():
        import_code = codes['imports']
        production_code = codes['production']
        
        if import_code in sd_data and production_code in sd_data:
            import_dates, import_vals = extract_time_series(sd_data[import_code])
            prod_dates, prod_vals = extract_time_series(sd_data[production_code])
            
            if import_vals and prod_vals:
                latest_imports = import_vals[-1]
                latest_production = prod_vals[-1]
                
                # Calculate import dependency ratio
                total_supply = latest_imports + latest_production
                if total_supply > 0:
                    dependency = (latest_imports / total_supply) * 100
                    product_names.append(product)
                    dependency_ratios.append(dependency)
    
    if not product_names:
        return go.Figure().update_layout(title="No import dependency data available")
    
    # Create bar chart
    colors = ['#c00000' if ratio > 50 else '#ff7f0e' if ratio > 25 else '#2ca02c' for ratio in dependency_ratios]
    
    fig = go.Figure(data=go.Bar(
        x=product_names,
        y=dependency_ratios,
        text=[f"{ratio:.1f}%" for ratio in dependency_ratios],
        textposition='auto',
        marker_color=colors
    ))
    
    # Add threshold lines
    fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="High Dependency (50%)")
    fig.add_hline(y=25, line_dash="dash", line_color="orange", annotation_text="Moderate Dependency (25%)")
    
    fig.update_layout(
        title="Import Dependency by Product<br><sub>Imports as % of Total Supply</sub>",
        xaxis_title="Product",
        yaxis_title="Import Dependency (%)",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for trade flow sankey
@callback(
    Output("trade-flow-sankey", "figure"),
    [Input("current-data-store-p14", "data")]
)
def update_trade_flow_sankey(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    # Create mock Sankey diagram for regional crude imports
    # In practice, this would use actual trade flow data
    
    padds = ['P1', 'P2', 'P3', 'P4', 'P5']
    import_codes = ['crude_imports_p1', 'crude_imports_p2', 'crude_imports_p3', 
                    'crude_imports_p4', 'crude_imports_p5']
    
    # Get import values by PADD
    padd_imports = []
    padd_names = []
    
    for i, (padd, code) in enumerate(zip(padds, import_codes)):
        if code in sd_data:
            dates, vals = extract_time_series(sd_data[code])
            if vals and vals[-1] > 0:  # Only include PADDs with imports
                padd_imports.append(vals[-1])
                padd_names.append(padd)
    
    if not padd_imports:
        return go.Figure().update_layout(title="No regional import data available")
    
    # Create simplified Sankey (bar chart representation due to complexity)
    fig = go.Figure(data=go.Bar(
        y=padd_names,
        x=padd_imports,
        orientation='h',
        marker_color=['#c00000', '#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd'][:len(padd_names)],
        text=[f"{val:,.0f} mb/d" for val in padd_imports],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Regional Crude Oil Import Flows by PADD<br><sub>Latest week data</sub>",
        xaxis_title="Import Volume (thousand barrels/day)",
        yaxis_title="PADD Region",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for net imports vs production
@callback(
    Output("net-imports-vs-production", "figure"),
    [Input("current-data-store-p14", "data")]
)
def update_net_imports_vs_production(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    if ('crude_imports' not in sd_data or 'crude_exports' not in sd_data 
        or 'crude_production' not in sd_data):
        return go.Figure().update_layout(title="Required data not available")
    
    # Extract time series
    import_dates, import_vals = extract_time_series(sd_data['crude_imports'])
    export_dates, export_vals = extract_time_series(sd_data['crude_exports'])
    prod_dates, prod_vals = extract_time_series(sd_data['crude_production'])
    
    # Align dates
    common_dates = sorted(set(import_dates) & set(export_dates) & set(prod_dates))
    
    net_imports = []
    production = []
    aligned_dates = []
    
    for date in common_dates:
        try:
            import_idx = import_dates.index(date)
            export_idx = export_dates.index(date)
            prod_idx = prod_dates.index(date)
            
            net_import = import_vals[import_idx] - export_vals[export_idx]
            prod_val = prod_vals[prod_idx]
            
            net_imports.append(net_import)
            production.append(prod_val)
            aligned_dates.append(date)
        except ValueError:
            continue
    
    if not aligned_dates:
        return go.Figure().update_layout(title="No aligned data available")
    
    fig = go.Figure()
    
    # Add net imports
    fig.add_trace(go.Scatter(
        x=aligned_dates,
        y=net_imports,
        mode='lines+markers',
        name='Net Imports',
        line=dict(color='#c00000', width=2),
        marker=dict(size=4)
    ))
    
    # Add production on secondary axis
    fig.add_trace(go.Scatter(
        x=aligned_dates,
        y=production,
        mode='lines+markers',
        name='US Production',
        line=dict(color='#2ca02c', width=2),
        marker=dict(size=4),
        yaxis='y2'
    ))
    
    # Add zero line for net imports
    fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Energy Independence")
    
    fig.update_layout(
        title="Net Crude Oil Imports vs US Production",
        xaxis_title="Date",
        yaxis=dict(
            title="Net Imports (mb/d)",
            side="left",
            color="#c00000"
        ),
        yaxis2=dict(
            title="US Production (mb/d)",
            side="right",
            overlaying="y",
            color="#2ca02c"
        ),
        hovermode='x unified',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for supply security gauge
@callback(
    Output("supply-security-gauge", "figure"),
    [Input("current-data-store-p14", "data")]
)
def update_supply_security_gauge(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    # Calculate supply security index based on multiple factors
    security_score = 50  # Default
    
    factors = []
    
    # Factor 1: Import dependency (lower is better)
    if 'crude_imports' in sd_data and 'crude_production' in sd_data:
        import_dates, import_vals = extract_time_series(sd_data['crude_imports'])
        prod_dates, prod_vals = extract_time_series(sd_data['crude_production'])
        
        if import_vals and prod_vals:
            latest_imports = import_vals[-1]
            latest_production = prod_vals[-1]
            
            total_supply = latest_imports + latest_production
            if total_supply > 0:
                import_dependency = (latest_imports / total_supply) * 100
                # Convert to security score (lower dependency = higher security)
                dependency_score = max(0, 100 - import_dependency * 2)
                factors.append(dependency_score)
    
    # Factor 2: Stock levels (days of supply proxy)
    if 'crude_stocks' in sd_data and 'crude_runs' in sd_data:
        stock_dates, stock_vals = extract_time_series(sd_data['crude_stocks'])
        runs_dates, runs_vals = extract_time_series(sd_data['crude_runs'])
        
        if stock_vals and runs_vals:
            latest_stocks = stock_vals[-1] * 1000  # Convert to barrels
            latest_runs = runs_vals[-1] * 7  # Convert to weekly consumption
            
            if latest_runs > 0:
                days_supply = latest_stocks / (latest_runs * 1000)
                # Normalize to 0-100 scale (30+ days = 100)
                stock_score = min(100, (days_supply / 30) * 100)
                factors.append(stock_score)
    
    # Factor 3: Production stability (lower volatility = higher security)
    if 'crude_production' in sd_data:
        prod_dates, prod_vals = extract_time_series(sd_data['crude_production'])
        
        if len(prod_vals) >= 12:  # Need at least 12 weeks of data
            recent_production = prod_vals[-12:]
            volatility = np.std(recent_production) / np.mean(recent_production) * 100
            # Convert to security score (lower volatility = higher security)
            stability_score = max(0, 100 - volatility * 10)
            factors.append(stability_score)
    
    # Calculate overall security score
    if factors:
        security_score = np.mean(factors)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = security_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Supply Security Index"},
        delta = {'reference': 75, 'position': "top"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#c00000"},
            'steps': [
                {'range': [0, 40], 'color': "#ffcccc"},
                {'range': [40, 60], 'color': "#ffeecc"},
                {'range': [60, 80], 'color': "#ccffcc"},
                {'range': [80, 100], 'color': "#ccffff"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(height=350)
    
    return fig

# Callback for product balance calendar
@callback(
    Output("product-balance-calendar", "figure"),
    [Input("current-data-store-p14", "data"),
     Input("product-balance-selector", "value")]
)
def update_product_balance_calendar(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    # Map product to data keys
    product_mapping = {
        'crude': 'crude_stocks',
        'gasoline': 'gasoline_stocks',
        'distillate': 'distillate_stocks'
    }
    
    if selected_product not in product_mapping:
        return go.Figure().update_layout(title="Product not supported")
    
    data_key = product_mapping[selected_product]
    
    if data_key not in sd_data:
        return go.Figure().update_layout(title=f"No {selected_product} data available")
    
    dates, values = extract_time_series(sd_data[data_key])
    
    if not dates:
        return go.Figure().update_layout(title="No time series data available")
    
    # Create calendar heatmap data
    df_calendar = pd.DataFrame({'date': dates, 'value': values})
    df_calendar['year'] = df_calendar['date'].dt.year
    df_calendar['month'] = df_calendar['date'].dt.month
    df_calendar['day'] = df_calendar['date'].dt.day
    df_calendar['week'] = df_calendar['date'].dt.isocalendar().week
    df_calendar['weekday'] = df_calendar['date'].dt.weekday
    
    # Get the last 12 weeks of data for a cleaner calendar view
    latest_date = df_calendar['date'].max()
    start_date = latest_date - pd.Timedelta(weeks=12)
    df_recent = df_calendar[df_calendar['date'] >= start_date].sort_values('date')
    
    if df_recent.empty:
        return go.Figure().update_layout(title="No recent data available")
    
    # Create weekly aggregated data
    weekly_data = df_recent.groupby([pd.Grouper(key='date', freq='W')])['value'].mean()
    
    # Calculate week-over-week changes
    weekly_changes = weekly_data.pct_change() * 100
    
    # Create a bar chart showing weekly stock levels with color coding for changes
    fig = go.Figure()
    
    # Determine colors based on week-over-week changes
    colors = []
    for i, change in enumerate(weekly_changes):
        if pd.isna(change) or abs(change) < 1:
            colors.append('#FFC107')  # Yellow for minimal change
        elif change > 0:
            colors.append('#4CAF50')  # Green for increase
        else:
            colors.append('#F44336')  # Red for decrease
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=weekly_data.index,
        y=weekly_data.values,
        marker_color=colors,
        text=[f"{val:,.0f}<br>{chg:+.1f}%" if not pd.isna(chg) else f"{val:,.0f}" 
              for val, chg in zip(weekly_data.values, weekly_changes)],
        textposition='auto',
        hovertemplate='Week: %{x|%Y-%m-%d}<br>Stock: %{y:,.0f} kb<extra></extra>'
    ))
    
    # Add average line
    avg_level = weekly_data.mean()
    fig.add_hline(y=avg_level, line_dash="dash", line_color="gray", 
                  annotation_text=f"12-week avg: {avg_level:,.0f}")
    
    fig.update_layout(
        title=f"{selected_product.title()} Weekly Stock Levels (Last 12 Weeks)",
        xaxis_title="Week Ending",
        yaxis_title="Stock Level (thousand barrels)",
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False
    )
    
    return fig

# Callback for trade statistics table
@callback(
    Output("trade-statistics-table", "children"),
    [Input("current-data-store-p14", "data")]
)
def update_trade_statistics_table(data):
    if not data:
        return html.Div("No data available")
    
    df = pd.DataFrame(data)
    sd_data = get_supply_demand_data(df)
    
    stats = []
    
    # Current trade volumes
    if 'crude_imports' in sd_data:
        dates, vals = extract_time_series(sd_data['crude_imports'])
        if vals:
            current_imports = vals[-1]
            weekly_change = vals[-1] - vals[-2] if len(vals) >= 2 else 0
            stats.extend([
                ("Crude Imports", f"{current_imports:,.0f} mb/d"),
                ("Import Change", f"{weekly_change:+.0f} mb/d")
            ])
    
    if 'crude_exports' in sd_data:
        dates, vals = extract_time_series(sd_data['crude_exports'])
        if vals:
            current_exports = vals[-1]
            weekly_change = vals[-1] - vals[-2] if len(vals) >= 2 else 0
            stats.extend([
                ("Crude Exports", f"{current_exports:,.0f} mb/d"),
                ("Export Change", f"{weekly_change:+.0f} mb/d")
            ])
    
    # Calculate net trade
    if 'crude_imports' in sd_data and 'crude_exports' in sd_data:
        import_dates, import_vals = extract_time_series(sd_data['crude_imports'])
        export_dates, export_vals = extract_time_series(sd_data['crude_exports'])
        
        if import_vals and export_vals:
            net_imports = import_vals[-1] - export_vals[-1]
            stats.append(("Net Imports", f"{net_imports:+.0f} mb/d"))
    
    # Energy independence indicator
    if 'crude_production' in sd_data and net_imports:
        prod_dates, prod_vals = extract_time_series(sd_data['crude_production'])
        if prod_vals:
            production = prod_vals[-1]
            independence = (production / (production + max(0, net_imports))) * 100
            stats.append(("Energy Independence", f"{independence:.1f}%"))
    
    # Product imports
    for product, key in [("Gasoline", "gasoline_imports"), ("Distillate", "distillate_imports")]:
        if key in sd_data:
            dates, vals = extract_time_series(sd_data[key])
            if vals:
                stats.append((f"{product} Imports", f"{vals[-1]:,.0f} mb/d"))
    
    if not stats:
        return html.Div("No trade statistics available")
    
    table_rows = []
    for stat, value in stats:
        color = "#2ca02c" if "+" in value else "#c00000" if "-" in value else "black"
        table_rows.append(
            html.Tr([
                html.Td(stat, style={"padding": "5px"}),
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
    Output("export-balance-btn-p14", "n_clicks"),
    [Input("export-balance-btn-p14", "n_clicks")],
    prevent_initial_call=True
)
def handle_export_balance(n_clicks):
    if n_clicks > 0:
        print("Export balance sheet functionality would be implemented here")
    return 0