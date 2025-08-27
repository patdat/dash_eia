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
    print(f"Error loading initial data for page2_12: {e}")
    # Create empty dataframe with minimal columns for initial load
    import pandas as pd
    df = pd.DataFrame()
    columnDefinitions = []

# Page layout for page 2_12 - Cushing vs Commercial Stocks Analysis
layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("Cushing Hub vs Commercial Stocks Analysis", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range-p12',
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
            html.Button("📊 Export Analysis", id="export-analysis-btn-p12", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),
    
    # Main content area with charts
    html.Div([
        # Top row - Primary comparison charts
        html.Div([
            html.Div([
                html.H3("Cushing vs US Commercial Crude Stocks", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="cushing-vs-commercial-time-series", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Cushing as % of US Commercial & PADD 3 Stocks", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="cushing-percentage-chart", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Middle row - Analysis charts  
        html.Div([
            html.Div([
                html.H3("Weekly Changes: Cushing vs Commercial", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="weekly-changes-comparison", style={"height": "400px"})
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Cushing-Commercial Spread Analysis", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="cushing-spread-analysis", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Bottom row - Advanced analytics
        html.Div([
            html.Div([
                html.H3("Cushing Inventory Level Gauge", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="cushing-inventory-gauge", style={"height": "350px"})
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Seasonal Pattern Analysis", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="seasonal-pattern-radar", style={"height": "350px"})
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Key Statistics", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div(id="key-statistics-table", style={"height": "350px", "padding": "10px", "backgroundColor": "#f8f8f8", "border": "1px solid #ddd"})
            ], style={"width": "32%"}),
        ], style={"display": "flex"}),
    ], style={"padding": "20px", "height": "85vh", "overflow": "auto"}),
    
    # Hidden stores
    dcc.Store(id='current-data-store-p12', data=df.to_dict('records') if not df.empty else [])
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# Helper function to get Cushing and Commercial stock data
def get_cushing_commercial_data(df):
    """Extract Cushing, US Commercial, and PADD 3 crude stock data"""
    if df.empty:
        return None, None, None
    
    # Cushing data
    cushing_data = df[df['id'] == 'W_EPC0_SAX_YCUOK_MBBL']
    # US Commercial data  
    commercial_data = df[df['id'] == 'WCESTUS1']
    # PADD 3 Commercial data
    padd3_data = df[df['id'] == 'WCESTP31']
    
    return (cushing_data.iloc[0] if not cushing_data.empty else None,
            commercial_data.iloc[0] if not commercial_data.empty else None,
            padd3_data.iloc[0] if not padd3_data.empty else None)

# Helper function to extract time series data
def extract_time_series(data_row):
    """Extract time series data from a data row"""
    if data_row is None:
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
    Output("current-data-store-p12", "data"),
    [Input("date-picker-range-p12", "start_date"),
     Input("date-picker-range-p12", "end_date")]
)
def update_data_store(start_date, end_date):
    try:
        df, _ = processor.get_data(start_date, end_date)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error updating data store: {e}")
        return []

# Callback for Cushing vs Commercial time series
@callback(
    Output("cushing-vs-commercial-time-series", "figure"),
    [Input("current-data-store-p12", "data")]
)
def update_cushing_vs_commercial(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    cushing_data, commercial_data, _ = get_cushing_commercial_data(df)
    
    fig = go.Figure()
    
    # Add Cushing data
    if cushing_data is not None:
        dates, values = extract_time_series(cushing_data)
        if dates and values:
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Cushing Hub',
                line=dict(color='#c00000', width=2),
                marker=dict(size=4)
            ))
    
    # Add Commercial data (normalized to same scale as Cushing for better visualization)
    if commercial_data is not None:
        dates_comm, values_comm = extract_time_series(commercial_data)
        if dates_comm and values_comm:
            # Scale commercial data to be comparable to Cushing (divide by ~20 to bring to similar range)
            scaled_values = [v/20 for v in values_comm]
            fig.add_trace(go.Scatter(
                x=dates_comm,
                y=scaled_values,
                mode='lines+markers',
                name='US Commercial (÷20)',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=4)
            ))
    
    # Update layout with single y-axis for better readability
    fig.update_layout(
        title="Cushing Hub vs US Commercial Crude Oil Stocks<br><sub>Commercial stocks scaled by factor of 20 for visualization</sub>",
        xaxis_title="Date",
        yaxis_title="Stock Level (thousand barrels)",
        hovermode='x unified',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for Cushing percentage chart
@callback(
    Output("cushing-percentage-chart", "figure"),
    [Input("current-data-store-p12", "data")]
)
def update_cushing_percentage(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    cushing_data, commercial_data, padd3_data = get_cushing_commercial_data(df)
    
    if cushing_data is None:
        return go.Figure().update_layout(title="Cushing data not available")
    
    fig = go.Figure()
    
    cushing_dates, cushing_values = extract_time_series(cushing_data)
    
    # Calculate Cushing as % of US Commercial Stocks
    if commercial_data is not None:
        commercial_dates, commercial_values = extract_time_series(commercial_data)
        common_dates = sorted(set(cushing_dates) & set(commercial_dates))
        
        us_percentages = []
        us_dates = []
        
        for date in common_dates:
            try:
                cushing_idx = cushing_dates.index(date)
                commercial_idx = commercial_dates.index(date)
                
                cushing_val = cushing_values[cushing_idx]
                commercial_val = commercial_values[commercial_idx]
                
                if commercial_val > 0:
                    percentage = (cushing_val / commercial_val) * 100
                    us_percentages.append(percentage)
                    us_dates.append(date)
            except (ValueError, ZeroDivisionError):
                continue
        
        if us_percentages:
            fig.add_trace(go.Scatter(
                x=us_dates,
                y=us_percentages,
                mode='lines+markers',
                name='% of US Commercial',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=4)
            ))
            
            # Add US average line
            us_avg = np.mean(us_percentages)
            fig.add_hline(
                y=us_avg,
                line_dash="dash",
                line_color="#1f77b4",
                annotation_text=f"US Avg: {us_avg:.1f}%",
                annotation_position="top left"
            )
    
    # Calculate Cushing as % of PADD 3 Stocks
    if padd3_data is not None:
        padd3_dates, padd3_values = extract_time_series(padd3_data)
        common_dates_p3 = sorted(set(cushing_dates) & set(padd3_dates))
        
        p3_percentages = []
        p3_dates = []
        
        for date in common_dates_p3:
            try:
                cushing_idx = cushing_dates.index(date)
                padd3_idx = padd3_dates.index(date)
                
                cushing_val = cushing_values[cushing_idx]
                padd3_val = padd3_values[padd3_idx]
                
                if padd3_val > 0:
                    percentage = (cushing_val / padd3_val) * 100
                    p3_percentages.append(percentage)
                    p3_dates.append(date)
            except (ValueError, ZeroDivisionError):
                continue
        
        if p3_percentages:
            fig.add_trace(go.Scatter(
                x=p3_dates,
                y=p3_percentages,
                mode='lines+markers',
                name='% of PADD 3',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=4)
            ))
            
            # Add PADD 3 average line
            p3_avg = np.mean(p3_percentages)
            fig.add_hline(
                y=p3_avg,
                line_dash="dash",
                line_color="#ff7f0e",
                annotation_text=f"P3 Avg: {p3_avg:.1f}%",
                annotation_position="bottom right"
            )
    
    fig.update_layout(
        title="Cushing Hub as Percentage of US Commercial & PADD 3 Stocks",
        xaxis_title="Date",
        yaxis_title="Percentage (%)",
        hovermode='x unified',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for weekly changes comparison
@callback(
    Output("weekly-changes-comparison", "figure"),
    [Input("current-data-store-p12", "data")]
)
def update_weekly_changes_comparison(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    cushing_data, commercial_data, _ = get_cushing_commercial_data(df)
    
    if cushing_data is None or commercial_data is None:
        return go.Figure().update_layout(title="Required data not available")
    
    # Calculate weekly changes
    cushing_dates, cushing_values = extract_time_series(cushing_data)
    commercial_dates, commercial_values = extract_time_series(commercial_data)
    
    def calculate_changes(dates, values):
        changes = []
        change_dates = []
        for i in range(1, len(values)):
            change = values[i] - values[i-1]
            changes.append(change)
            change_dates.append(dates[i])
        return change_dates, changes
    
    cushing_change_dates, cushing_changes = calculate_changes(cushing_dates, cushing_values)
    commercial_change_dates, commercial_changes = calculate_changes(commercial_dates, commercial_values)
    
    fig = go.Figure()
    
    # Add Cushing changes
    if cushing_changes:
        fig.add_trace(go.Bar(
            x=cushing_change_dates,
            y=cushing_changes,
            name='Cushing Weekly Change',
            marker_color=['#2ca02c' if x >= 0 else '#c00000' for x in cushing_changes],
            opacity=0.7
        ))
    
    # Add commercial changes (scaled down for visibility)
    if commercial_changes:
        scaled_commercial = [x/50 for x in commercial_changes]  # Scale down by factor of 50
        fig.add_trace(go.Scatter(
            x=commercial_change_dates,
            y=scaled_commercial,
            mode='lines+markers',
            name='Commercial Weekly Change (÷50)',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4),
            yaxis='y2'
        ))
    
    fig.update_layout(
        title="Weekly Stock Changes: Cushing vs Commercial",
        xaxis_title="Date",
        yaxis=dict(
            title="Cushing Change (thousand barrels)",
            side="left"
        ),
        yaxis2=dict(
            title="Commercial Change (÷50, thousand barrels)",
            side="right",
            overlaying="y"
        ),
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for Cushing spread analysis
@callback(
    Output("cushing-spread-analysis", "figure"),
    [Input("current-data-store-p12", "data")]
)
def update_cushing_spread_analysis(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    cushing_data, commercial_data, _ = get_cushing_commercial_data(df)
    
    if cushing_data is None or commercial_data is None:
        return go.Figure().update_layout(title="Required data not available")
    
    # Calculate spread (difference between Cushing and proportional commercial)
    cushing_dates, cushing_values = extract_time_series(cushing_data)
    commercial_dates, commercial_values = extract_time_series(commercial_data)
    
    # Align dates and calculate spread
    common_dates = sorted(set(cushing_dates) & set(commercial_dates))
    spreads = []
    spread_dates = []
    
    for date in common_dates:
        try:
            cushing_idx = cushing_dates.index(date)
            commercial_idx = commercial_dates.index(date)
            
            cushing_val = cushing_values[cushing_idx]
            commercial_val = commercial_values[commercial_idx]
            
            # Calculate spread as deviation from expected ratio
            expected_cushing = commercial_val * 0.08  # Assume Cushing should be ~8% of commercial
            spread = cushing_val - expected_cushing
            
            spreads.append(spread)
            spread_dates.append(date)
        except ValueError:
            continue
    
    if not spreads:
        return go.Figure().update_layout(title="No spread data available")
    
    fig = go.Figure()
    
    # Color bars based on positive/negative spread
    colors = ['#2ca02c' if x >= 0 else '#c00000' for x in spreads]
    
    fig.add_trace(go.Bar(
        x=spread_dates,
        y=spreads,
        name='Cushing Spread',
        marker_color=colors,
        text=[f"{val:+.0f}" for val in spreads],
        textposition='outside'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    
    fig.update_layout(
        title="Cushing-Commercial Spread Analysis<br><sub>Positive = Above Expected, Negative = Below Expected</sub>",
        xaxis_title="Date",
        yaxis_title="Spread (thousand barrels)",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for Cushing inventory gauge
@callback(
    Output("cushing-inventory-gauge", "figure"),
    [Input("current-data-store-p12", "data")]
)
def update_cushing_inventory_gauge(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    cushing_data, _, _ = get_cushing_commercial_data(df)
    
    if cushing_data is None:
        return go.Figure().update_layout(title="Cushing data not available")
    
    dates, values = extract_time_series(cushing_data)
    
    if not values:
        return go.Figure().update_layout(title="No Cushing data available")
    
    current_level = values[-1]
    max_level = max(values)
    min_level = min(values)
    avg_level = np.mean(values)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_level,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Current Level (kb)"},
        delta = {'reference': avg_level, 'position': "top"},
        gauge = {
            'axis': {'range': [None, max_level * 1.1]},
            'bar': {'color': "#c00000"},
            'steps': [
                {'range': [0, min_level], 'color': "#ffcccc"},
                {'range': [min_level, avg_level], 'color': "#ffeecc"},
                {'range': [avg_level, max_level], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': avg_level
            }
        }
    ))
    
    fig.update_layout(height=350)
    
    return fig

# Callback for seasonal pattern radar
@callback(
    Output("seasonal-pattern-radar", "figure"),
    [Input("current-data-store-p12", "data")]
)
def update_seasonal_pattern_radar(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    cushing_data, _, _ = get_cushing_commercial_data(df)
    
    if cushing_data is None:
        return go.Figure().update_layout(title="Cushing data not available")
    
    dates, values = extract_time_series(cushing_data)
    
    if not dates:
        return go.Figure().update_layout(title="No time series data available")
    
    # Create seasonal analysis by month
    monthly_data = {}
    for date, value in zip(dates, values):
        month = date.strftime('%B')
        if month not in monthly_data:
            monthly_data[month] = []
        monthly_data[month].append(value)
    
    # Calculate average by month
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    monthly_avgs = []
    for month in months:
        if month in monthly_data:
            monthly_avgs.append(np.mean(monthly_data[month]))
        else:
            monthly_avgs.append(0)
    
    # Normalize for radar chart (0-100 scale)
    if max(monthly_avgs) > 0:
        normalized_avgs = [(val / max(monthly_avgs)) * 100 for val in monthly_avgs]
    else:
        normalized_avgs = monthly_avgs
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized_avgs,
        theta=months,
        fill='toself',
        name='Cushing Seasonal Pattern',
        line_color='#c00000'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title="Cushing Seasonal Pattern (Normalized)",
        height=350
    )
    
    return fig

# Callback for key statistics table
@callback(
    Output("key-statistics-table", "children"),
    [Input("current-data-store-p12", "data")]
)
def update_key_statistics(data):
    if not data:
        return html.Div("No data available")
    
    df = pd.DataFrame(data)
    cushing_data, commercial_data, _ = get_cushing_commercial_data(df)
    
    if cushing_data is None or commercial_data is None:
        return html.Div("Required data not available")
    
    # Extract time series
    cushing_dates, cushing_values = extract_time_series(cushing_data)
    commercial_dates, commercial_values = extract_time_series(commercial_data)
    
    if not cushing_values or not commercial_values:
        return html.Div("No time series data available")
    
    # Calculate statistics
    stats = []
    
    # Current levels
    current_cushing = cushing_values[-1] if cushing_values else 0
    current_commercial = commercial_values[-1] if commercial_values else 0
    current_ratio = (current_cushing / current_commercial * 100) if current_commercial > 0 else 0
    
    # Changes
    cushing_change = cushing_values[-1] - cushing_values[-2] if len(cushing_values) >= 2 else 0
    commercial_change = commercial_values[-1] - commercial_values[-2] if len(commercial_values) >= 2 else 0
    
    # Historical stats
    cushing_avg = np.mean(cushing_values)
    cushing_max = max(cushing_values)
    cushing_min = min(cushing_values)
    
    stats_html = html.Div([
        html.Table([
            html.Tr([html.Th("Metric", style={"padding": "5px", "backgroundColor": "#f0f0f0"}), 
                    html.Th("Value", style={"padding": "5px", "backgroundColor": "#f0f0f0"})]),
            html.Tr([html.Td("Current Cushing", style={"padding": "5px"}), 
                    html.Td(f"{current_cushing:,.0f} kb", style={"padding": "5px"})]),
            html.Tr([html.Td("Weekly Change", style={"padding": "5px"}), 
                    html.Td(f"{cushing_change:+.0f} kb", style={"padding": "5px", "color": "#2ca02c" if cushing_change >= 0 else "#c00000"})]),
            html.Tr([html.Td("% of Commercial", style={"padding": "5px"}), 
                    html.Td(f"{current_ratio:.1f}%", style={"padding": "5px"})]),
            html.Tr([html.Td("Historical Avg", style={"padding": "5px"}), 
                    html.Td(f"{cushing_avg:,.0f} kb", style={"padding": "5px"})]),
            html.Tr([html.Td("Historical Max", style={"padding": "5px"}), 
                    html.Td(f"{cushing_max:,.0f} kb", style={"padding": "5px"})]),
            html.Tr([html.Td("Historical Min", style={"padding": "5px"}), 
                    html.Td(f"{cushing_min:,.0f} kb", style={"padding": "5px"})]),
            html.Tr([html.Td("Capacity Usage", style={"padding": "5px"}), 
                    html.Td(f"{(current_cushing/80000)*100:.1f}%", style={"padding": "5px"})]),  # Assuming 80M barrel capacity
        ], style={"width": "100%", "border": "1px solid #ddd", "borderCollapse": "collapse"})
    ])
    
    return stats_html

# Export callback
@callback(
    Output("export-analysis-btn-p12", "n_clicks"),
    [Input("export-analysis-btn-p12", "n_clicks")],
    prevent_initial_call=True
)
def handle_export_analysis(n_clicks):
    if n_clicks > 0:
        # In a real implementation, this would trigger a download
        print("Export analysis functionality would be implemented here")
    return 0