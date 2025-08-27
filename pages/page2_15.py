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
    print(f"Error loading initial data for page2_15: {e}")
    # Create empty dataframe with minimal columns for initial load
    import pandas as pd
    df = pd.DataFrame()
    columnDefinitions = []

# Page layout for page 2_15 - Advanced Time Series & Anomaly Detection
layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("Advanced Time Series & Anomaly Detection", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range-p15',
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
            html.Button("📊 Export Insights", id="export-insights-btn-p15", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),
    
    # Main content area with charts
    html.Div([
        # Top row - Time series analysis
        html.Div([
            html.Div([
                html.H3("Year-over-Year Comparison Analysis", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    dcc.Dropdown(
                        id='yoy-product-selector',
                        options=[
                            {'label': 'Crude Oil Stocks', 'value': 'WCESTUS1'},
                            {'label': 'Gasoline Stocks', 'value': 'WGTSTUS1'},
                            {'label': 'Distillate Stocks', 'value': 'WDISTUS1'},
                            {'label': 'Crude Production', 'value': 'WCRFPUS2'}
                        ],
                        value='WCESTUS1',
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="yoy-comparison-chart", style={"height": "350px"})
                ])
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Z-Score Anomaly Detection", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    dcc.Dropdown(
                        id='anomaly-product-selector',
                        options=[
                            {'label': 'Crude Oil Stocks', 'value': 'WCESTUS1'},
                            {'label': 'Gasoline Stocks', 'value': 'WGTSTUS1'},
                            {'label': 'Distillate Stocks', 'value': 'WDISTUS1'},
                            {'label': 'Refinery Utilization', 'value': 'W_NA_YUP_R30_PER'}
                        ],
                        value='WCESTUS1',
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="anomaly-detection-chart", style={"height": "350px"})
                ])
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Middle row - Advanced analytics
        html.Div([
            html.Div([
                html.H3("Moving Average Convergence Divergence", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    dcc.Dropdown(
                        id='macd-product-selector',
                        options=[
                            {'label': 'Crude Oil Stocks', 'value': 'WCESTUS1'},
                            {'label': 'Gasoline Stocks', 'value': 'WGTSTUS1'},
                            {'label': 'Distillate Stocks', 'value': 'WDISTUS1'},
                            {'label': 'Crude Imports', 'value': 'WCEIMUS2'}
                        ],
                        value='WCESTUS1',
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="macd-chart", style={"height": "350px"})
                ])
            ], style={"width": "49%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Correlation Matrix Heatmap", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                dcc.Graph(id="correlation-matrix-heatmap", style={"height": "400px"})
            ], style={"width": "49%"}),
        ], style={"display": "flex", "marginBottom": "20px"}),
        
        # Bottom row - Insights and statistics
        html.Div([
            html.Div([
                html.H3("Statistical Insights", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div(id="statistical-insights-table", style={"height": "350px", "padding": "10px", "backgroundColor": "#f8f8f8", "border": "1px solid #ddd", "overflow": "auto"})
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Trend Decomposition", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    dcc.Dropdown(
                        id='decomposition-product-selector',
                        options=[
                            {'label': 'Crude Oil Stocks', 'value': 'WCESTUS1'},
                            {'label': 'Gasoline Stocks', 'value': 'WGTSTUS1'},
                            {'label': 'Distillate Stocks', 'value': 'WDISTUS1'}
                        ],
                        value='WCESTUS1',
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="trend-decomposition-chart", style={"height": "300px"})
                ])
            ], style={"width": "32%", "marginRight": "2%"}),
            
            html.Div([
                html.H3("Forecast Confidence Intervals", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Div([
                    dcc.Dropdown(
                        id='forecast-product-selector',
                        options=[
                            {'label': 'Crude Oil Stocks', 'value': 'WCESTUS1'},
                            {'label': 'Gasoline Stocks', 'value': 'WGTSTUS1'},
                            {'label': 'Distillate Stocks', 'value': 'WDISTUS1'}
                        ],
                        value='WCESTUS1',
                        style={"marginBottom": "10px"}
                    ),
                    dcc.Graph(id="forecast-intervals-chart", style={"height": "300px"})
                ])
            ], style={"width": "32%"}),
        ], style={"display": "flex"}),
    ], style={"padding": "20px", "height": "85vh", "overflow": "auto"}),
    
    # Hidden stores
    dcc.Store(id='current-data-store-p15', data=df.to_dict('records') if not df.empty else [])
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

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
    Output("current-data-store-p15", "data"),
    [Input("date-picker-range-p15", "start_date"),
     Input("date-picker-range-p15", "end_date")]
)
def update_data_store(start_date, end_date):
    try:
        df, _ = processor.get_data(start_date, end_date)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error updating data store: {e}")
        return []

# Callback for YoY comparison chart
@callback(
    Output("yoy-comparison-chart", "figure"),
    [Input("current-data-store-p15", "data"),
     Input("yoy-product-selector", "value")]
)
def update_yoy_comparison_chart(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    product_data = df[df['id'] == selected_product]
    
    if product_data.empty:
        return go.Figure().update_layout(title="Product data not available")
    
    dates, values = extract_time_series(product_data.iloc[0])
    
    if len(dates) < 52:  # Need at least a year of data
        return go.Figure().update_layout(title="Insufficient data for YoY comparison")
    
    # Create DataFrame for easier manipulation
    ts_df = pd.DataFrame({'date': dates, 'value': values})
    ts_df['year'] = ts_df['date'].dt.year
    ts_df['week'] = ts_df['date'].dt.isocalendar().week
    
    # Get last 3-5 years depending on data range
    all_years = sorted(ts_df['year'].unique())
    if len(all_years) <= 3:
        recent_years = all_years
    else:
        recent_years = all_years[-3:]  # Last 3 years for clarity
    
    fig = go.Figure()
    colors = ['#c00000', '#1f77b4', '#ff7f0e']
    
    for i, year in enumerate(recent_years):
        year_data = ts_df[ts_df['year'] == year].copy()
        year_data = year_data.sort_values('week')
        
        fig.add_trace(go.Scatter(
            x=year_data['week'],
            y=year_data['value'],
            mode='lines+markers',
            name=str(year),
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=f"Year-over-Year Comparison: {product_data.iloc[0]['name']}",
        xaxis=dict(
            title="Week of Year",
            range=[1, 52],
            dtick=4
        ),
        yaxis_title=product_data.iloc[0]['uom'],
        hovermode='x unified',
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for anomaly detection chart
@callback(
    Output("anomaly-detection-chart", "figure"),
    [Input("current-data-store-p15", "data"),
     Input("anomaly-product-selector", "value")]
)
def update_anomaly_detection_chart(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    product_data = df[df['id'] == selected_product]
    
    if product_data.empty:
        return go.Figure().update_layout(title="Product data not available")
    
    dates, values = extract_time_series(product_data.iloc[0])
    
    if len(values) < 20:  # Need sufficient data for z-score calculation
        return go.Figure().update_layout(title="Insufficient data for anomaly detection")
    
    # For long date ranges, sample data to avoid overcrowding
    if len(values) > 200:
        # Sample every nth point to keep ~200 points
        step = len(values) // 200
        dates_sampled = dates[::step]
        values_sampled = values[::step]
    else:
        dates_sampled = dates
        values_sampled = values
    
    # Calculate z-scores on sampled data
    values_array = np.array(values_sampled)
    rolling_mean = pd.Series(values_array).rolling(window=min(12, len(values_array)//4), min_periods=3).mean()
    rolling_std = pd.Series(values_array).rolling(window=min(12, len(values_array)//4), min_periods=3).std()
    
    z_scores = (values_array - rolling_mean) / rolling_std
    
    # Identify anomalies (|z-score| > 2)
    anomaly_threshold = 2
    anomalies = np.abs(z_scores) > anomaly_threshold
    
    fig = go.Figure()
    
    # Add main time series (sampled for clarity)
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=values_sampled,
        mode='lines+markers',
        name='Actual Values',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=3)
    ))
    
    # Add rolling mean
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=rolling_mean,
        mode='lines',
        name='Rolling Mean',
        line=dict(color='#2ca02c', width=2, dash='dash')
    ))
    
    # Highlight anomalies
    anomaly_dates = [date for i, date in enumerate(dates_sampled) if pd.notna(anomalies[i]) and anomalies[i]]
    anomaly_values = [value for i, value in enumerate(values_sampled) if pd.notna(anomalies[i]) and anomalies[i]]
    
    if anomaly_dates:
        fig.add_trace(go.Scatter(
            x=anomaly_dates,
            y=anomaly_values,
            mode='markers',
            name='Anomalies',
            marker=dict(color='#c00000', size=8, symbol='x')
        ))
    
    # Add confidence bands (simplified)
    upper_band = rolling_mean + 2 * rolling_std
    lower_band = rolling_mean - 2 * rolling_std
    
    # Only show confidence bands if we have valid data
    valid_indices = ~(pd.isna(upper_band) | pd.isna(lower_band))
    if valid_indices.any():
        fig.add_trace(go.Scatter(
            x=[d for i, d in enumerate(dates_sampled) if valid_indices[i]],
            y=[v for i, v in enumerate(upper_band) if valid_indices[i]],
            mode='lines',
            name='Upper Threshold',
            line=dict(color='red', width=1, dash='dot'),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=[d for i, d in enumerate(dates_sampled) if valid_indices[i]],
            y=[v for i, v in enumerate(lower_band) if valid_indices[i]],
            mode='lines',
            name='Lower Threshold',
            line=dict(color='red', width=1, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.1)',
            showlegend=False
        ))
    
    fig.update_layout(
        title=f"Z-Score Anomaly Detection: {product_data.iloc[0]['name']}<br><sub>Red X marks indicate statistical anomalies (|z-score| > 2)</sub>",
        xaxis_title="Date",
        yaxis_title=product_data.iloc[0]['uom'],
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for MACD chart
@callback(
    Output("macd-chart", "figure"),
    [Input("current-data-store-p15", "data"),
     Input("macd-product-selector", "value")]
)
def update_macd_chart(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    product_data = df[df['id'] == selected_product]
    
    if product_data.empty:
        return go.Figure().update_layout(title="Product data not available")
    
    dates, values = extract_time_series(product_data.iloc[0])
    
    if len(values) < 26:  # Need at least 26 periods for MACD
        return go.Figure().update_layout(title="Insufficient data for MACD calculation")
    
    # For long date ranges, sample data to avoid overcrowding
    if len(values) > 300:
        step = len(values) // 300
        dates_sampled = dates[::step]
        values_sampled = values[::step]
    else:
        dates_sampled = dates
        values_sampled = values
    
    # Calculate MACD on sampled data
    ts_series = pd.Series(values_sampled)
    ema12 = ts_series.ewm(span=12).mean()
    ema26 = ts_series.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()
    histogram = macd_line - signal_line
    
    # Create subplots with better spacing
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.15,
        subplot_titles=('Price & Moving Averages', 'MACD Indicator')
    )
    
    # Price chart with EMAs (using sampled data)
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=values_sampled,
        mode='lines',
        name='Price',
        line=dict(color='#1f77b4', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=ema12,
        mode='lines',
        name='EMA 12',
        line=dict(color='#ff7f0e', width=1, dash='dash')
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=ema26,
        mode='lines',
        name='EMA 26',
        line=dict(color='#2ca02c', width=1, dash='dash')
    ), row=1, col=1)
    
    # MACD chart (using sampled data)
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=macd_line,
        mode='lines',
        name='MACD',
        line=dict(color='#c00000', width=2)
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=signal_line,
        mode='lines',
        name='Signal',
        line=dict(color='#ff7f0e', width=2)
    ), row=2, col=1)
    
    # MACD histogram (only show every few bars for clarity)
    if len(histogram) > 100:
        hist_step = len(histogram) // 50  # Show only ~50 bars
        hist_dates = dates_sampled[::hist_step]
        hist_values = histogram[::hist_step]
    else:
        hist_dates = dates_sampled
        hist_values = histogram
        
    fig.add_trace(go.Bar(
        x=hist_dates,
        y=hist_values,
        name='Histogram',
        marker_color=['#2ca02c' if x >= 0 else '#c00000' for x in hist_values],
        opacity=0.6
    ), row=2, col=1)
    
    fig.update_layout(
        title=f"MACD Analysis: {product_data.iloc[0]['name']}",
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True
    )
    
    return fig

# Callback for correlation matrix heatmap
@callback(
    Output("correlation-matrix-heatmap", "figure"),
    [Input("current-data-store-p15", "data")]
)
def update_correlation_matrix_heatmap(data):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    
    # Select key petroleum products for correlation analysis
    key_products = {
        'WCESTUS1': 'Crude Stocks',
        'WGTSTUS1': 'Gasoline Stocks', 
        'WDISTUS1': 'Distillate Stocks',
        'WKJSTUS1': 'Jet Fuel Stocks',
        'WCRRIUS2': 'Crude Runs',
        'WCEIMUS2': 'Crude Imports',
        'WGFRPUS2': 'Gasoline Production'
    }
    
    # Extract time series for each product
    correlation_data = {}
    
    for product_id, product_name in key_products.items():
        product_data = df[df['id'] == product_id]
        if not product_data.empty:
            dates, values = extract_time_series(product_data.iloc[0])
            if len(values) >= 20:  # Need sufficient data
                correlation_data[product_name] = pd.Series(values, index=dates)
    
    if len(correlation_data) < 3:
        return go.Figure().update_layout(title="Insufficient data for correlation analysis")
    
    # Create DataFrame and calculate correlation
    corr_df = pd.DataFrame(correlation_data)
    
    # Align all series to common dates
    corr_df = corr_df.dropna()
    
    if corr_df.empty:
        return go.Figure().update_layout(title="No overlapping data for correlation")
    
    correlation_matrix = corr_df.corr()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=correlation_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Petroleum Products Correlation Matrix",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Callback for statistical insights table
@callback(
    Output("statistical-insights-table", "children"),
    [Input("current-data-store-p15", "data")]
)
def update_statistical_insights_table(data):
    if not data:
        return html.Div("No data available")
    
    df = pd.DataFrame(data)
    
    insights = []
    
    # Analyze key products
    key_products = {
        'WCESTUS1': 'Crude Oil Stocks',
        'WGTSTUS1': 'Gasoline Stocks',
        'WDISTUS1': 'Distillate Stocks'
    }
    
    for product_id, product_name in key_products.items():
        product_data = df[df['id'] == product_id]
        if not product_data.empty:
            dates, values = extract_time_series(product_data.iloc[0])
            
            if len(values) >= 10:
                # Calculate statistics
                current_value = values[-1]
                mean_value = np.mean(values)
                std_value = np.std(values)
                min_value = min(values)
                max_value = max(values)
                
                # Percentile ranking
                percentile = (sum(v <= current_value for v in values) / len(values)) * 100
                
                # Volatility (coefficient of variation)
                cv = (std_value / mean_value) * 100 if mean_value != 0 else 0
                
                # Trend analysis (last 12 weeks slope)
                if len(values) >= 12:
                    recent_values = values[-12:]
                    x = np.arange(len(recent_values))
                    slope = np.polyfit(x, recent_values, 1)[0]
                    trend = "Rising" if slope > 0 else "Falling" if slope < 0 else "Stable"
                else:
                    trend = "N/A"
                
                insights.extend([
                    html.H4(product_name, style={"color": "#c00000", "margin": "10px 0 5px 0"}),
                    html.P(f"Current: {current_value:,.0f}", style={"margin": "2px 0"}),
                    html.P(f"Percentile: {percentile:.0f}%", style={"margin": "2px 0"}),
                    html.P(f"Volatility: {cv:.1f}%", style={"margin": "2px 0"}),
                    html.P(f"Trend: {trend}", style={"margin": "2px 0"}),
                    html.Hr(style={"margin": "10px 0"})
                ])
    
    if not insights:
        return html.Div("No insights available")
    
    return html.Div(insights)

# Callback for trend decomposition chart
@callback(
    Output("trend-decomposition-chart", "figure"),
    [Input("current-data-store-p15", "data"),
     Input("decomposition-product-selector", "value")]
)
def update_trend_decomposition_chart(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    product_data = df[df['id'] == selected_product]
    
    if product_data.empty:
        return go.Figure().update_layout(title="Product data not available")
    
    dates, values = extract_time_series(product_data.iloc[0])
    
    if len(values) < 52:  # Need at least a year of data
        return go.Figure().update_layout(title="Insufficient data for trend decomposition")
    
    # For long date ranges, sample data
    if len(values) > 300:
        step = len(values) // 300
        dates_sampled = dates[::step]
        values_sampled = values[::step]
    else:
        dates_sampled = dates
        values_sampled = values
    
    # Simple trend decomposition using moving averages
    ts_series = pd.Series(values_sampled)
    
    # Adjust window size based on data length
    window_size = min(52, len(values_sampled) // 4)
    if window_size < 4:
        window_size = 4
    
    # Trend (moving average)
    trend = ts_series.rolling(window=window_size, center=True, min_periods=1).mean()
    
    fig = go.Figure()
    
    # Plot original data (lightly)
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=values_sampled,
        mode='lines',
        name='Original Data',
        line=dict(color='lightgray', width=1),
        opacity=0.5
    ))
    
    # Plot trend
    fig.add_trace(go.Scatter(
        x=dates_sampled,
        y=trend,
        mode='lines',
        name='Trend',
        line=dict(color='#c00000', width=3)
    ))
    
    fig.update_layout(
        title=f"Trend Decomposition: {product_data.iloc[0]['name']}",
        xaxis_title="Date",
        yaxis_title=product_data.iloc[0]['uom'],
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for forecast intervals chart
@callback(
    Output("forecast-intervals-chart", "figure"),
    [Input("current-data-store-p15", "data"),
     Input("forecast-product-selector", "value")]
)
def update_forecast_intervals_chart(data, selected_product):
    if not data:
        return go.Figure().update_layout(title="No data available")
    
    df = pd.DataFrame(data)
    product_data = df[df['id'] == selected_product]
    
    if product_data.empty:
        return go.Figure().update_layout(title="Product data not available")
    
    dates, values = extract_time_series(product_data.iloc[0])
    
    if len(values) < 20:
        return go.Figure().update_layout(title="Insufficient data for forecasting")
    
    # For long date ranges, use recent data for forecast
    if len(values) > 100:
        # Use last 100 points for forecast calculation
        recent_dates = dates[-100:]
        recent_values = values[-100:]
        # But show last 50 points for visualization
        display_dates = dates[-50:]
        display_values = values[-50:]
    else:
        recent_dates = dates
        recent_values = values
        display_dates = dates
        display_values = values
    
    # Simple forecast using exponential smoothing on recent data
    ts_series = pd.Series(recent_values)
    
    # Calculate exponentially weighted moving average
    alpha = 0.3  # Smoothing parameter
    ewma = ts_series.ewm(alpha=alpha).mean()
    
    # Calculate forecast (simple extension of trend)
    recent_trend = ewma.iloc[-min(5, len(ewma)):].diff().mean()
    last_value = ewma.iloc[-1]
    
    # Generate 8-week forecast
    forecast_periods = 8
    forecast_values = []
    for i in range(forecast_periods):
        forecast_val = last_value + (i + 1) * recent_trend
        forecast_values.append(forecast_val)
    
    # Generate forecast dates
    last_date = recent_dates[-1]
    forecast_dates = [last_date + pd.Timedelta(weeks=i+1) for i in range(forecast_periods)]
    
    # Calculate confidence intervals based on historical volatility
    historical_std = ts_series.rolling(window=min(12, len(ts_series)//2), min_periods=3).std().iloc[-1]
    
    if pd.notna(historical_std) and historical_std > 0:
        upper_confidence = [val + 1.96 * historical_std * np.sqrt(i+1) for i, val in enumerate(forecast_values)]
        lower_confidence = [val - 1.96 * historical_std * np.sqrt(i+1) for i, val in enumerate(forecast_values)]
    else:
        # Fallback if std calculation fails
        std_estimate = np.std(recent_values) if len(recent_values) > 1 else abs(recent_values[-1] * 0.1)
        upper_confidence = [val + 1.96 * std_estimate * np.sqrt(i+1) for i, val in enumerate(forecast_values)]
        lower_confidence = [val - 1.96 * std_estimate * np.sqrt(i+1) for i, val in enumerate(forecast_values)]
    
    fig = go.Figure()
    
    # Historical data (show recent portion for clarity)
    fig.add_trace(go.Scatter(
        x=display_dates,
        y=display_values,
        mode='lines+markers',
        name='Historical',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#c00000', width=2, dash='dash'),
        marker=dict(size=4)
    ))
    
    # Confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=upper_confidence,
        mode='lines',
        name='95% Confidence',
        line=dict(color='red', width=1, dash='dot'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=lower_confidence,
        mode='lines',
        name='95% Confidence',
        line=dict(color='red', width=1, dash='dot'),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.1)',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"8-Week Forecast: {product_data.iloc[0]['name']}<br><sub>With 95% confidence intervals</sub>",
        xaxis_title="Date",
        yaxis_title=product_data.iloc[0]['uom'],
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# Export callback
@callback(
    Output("export-insights-btn-p15", "n_clicks"),
    [Input("export-insights-btn-p15", "n_clicks")],
    prevent_initial_call=True
)
def handle_export_insights(n_clicks):
    if n_clicks > 0:
        print("Export insights functionality would be implemented here")
    return 0