import pandas as pd
import numpy as np
from dash import html, dash_table, dcc, Input, Output, callback
from dash.dash_table.Format import Format
import plotly.graph_objects as go
from src.cli.cli_data_processor import CLIDataProcessor
from datetime import datetime, timedelta
from app import app
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA

processor = CLIDataProcessor()

def create_arima_forecast(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    # Fit ARIMA model with automatic parameter selection
    try:
        from pmdarima import auto_arima
        # Use auto_arima for better parameter selection
        auto_model = auto_arima(monthly, 
                               seasonal=True, 
                               m=12,  # monthly seasonality
                               suppress_warnings=True,
                               stepwise=True,
                               trace=False,
                               max_p=3, max_q=3, max_d=2,
                               max_P=2, max_Q=2, max_D=1)
        
        # Get forecast with proper confidence intervals
        forecast_result = auto_model.predict(n_periods=12, return_conf_int=True)
        forecast = forecast_result[0]
        conf_int = forecast_result[1]
        lower_bound = conf_int[:, 0]
        upper_bound = conf_int[:, 1]
        
        future_dates = pd.date_range(start=monthly.index[-1] + pd.DateOffset(months=1), periods=12, freq='MS')
        
    except:
        # Enhanced ARIMA with seasonal decomposition
        try:
            # Try SARIMA model with seasonal parameters
            model = ARIMA(monthly, order=(1,1,1), seasonal_order=(1,1,1,12))
            fitted_model = model.fit()
            
            # Get forecast with prediction intervals
            forecast_df = fitted_model.get_forecast(steps=12)
            forecast = forecast_df.predicted_mean
            conf_int = forecast_df.conf_int(alpha=0.05)
            lower_bound = conf_int.iloc[:, 0]
            upper_bound = conf_int.iloc[:, 1]
            
        except:
            # Fallback to ARIMA with trend and seasonality
            decomposition = seasonal_decompose(monthly[-36:], model='multiplicative', period=12)
            seasonal_factor = decomposition.seasonal[-12:].values
            
            # Deseasonalize the data
            deseasonalized = monthly / decomposition.seasonal.reindex(monthly.index, method='ffill').fillna(1)
            
            # Fit ARIMA on deseasonalized data
            model = ARIMA(deseasonalized, order=(2,1,2))
            fitted_model = model.fit()
            forecast_deseasonalized = fitted_model.forecast(steps=12)
            
            # Reapply seasonality
            forecast = forecast_deseasonalized * np.tile(seasonal_factor, 1)[:12]
            
            # Calculate more realistic confidence intervals
            residuals = fitted_model.resid
            forecast_std = np.std(residuals) * np.sqrt(1 + np.arange(1, 13) * 0.1)
            upper_bound = forecast + 1.96 * forecast_std
            lower_bound = forecast - 1.96 * forecast_std
        
        future_dates = pd.date_range(start=monthly.index[-1] + pd.DateOffset(months=1), periods=12, freq='MS')
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines',
        name='Historical',
        line=dict(color='#2E86AB', width=2)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=forecast,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#A23B72', width=2, dash='dash'),
        marker=dict(size=8)
    ))
    
    # Confidence intervals
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=upper_bound,
        mode='lines',
        name='Upper Bound (95% CI)',
        line=dict(color='gray', width=1, dash='dot'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=lower_bound,
        mode='lines',
        name='Lower Bound (95% CI)',
        line=dict(color='gray', width=1, dash='dot'),
        fill='tonexty',
        fillcolor='rgba(128,128,128,0.2)',
        showlegend=False
    ))
    
    # Calculate y-axis range for better visibility
    all_values = np.concatenate([monthly.values[-24:], forecast, upper_bound, lower_bound])
    y_min = np.nanmin(all_values) * 0.95
    y_max = np.nanmax(all_values) * 1.05
    
    # Add a vertical line at the forecast start
    fig.add_vline(x=monthly.index[-1], 
                  line_dash="dash", 
                  line_color="gray", 
                  opacity=0.5,
                  annotation_text="Forecast Start")
    
    fig.update_layout(
        title='12-Month ARIMA Forecast',
        xaxis_title='Date',
        yaxis_title='Volume (kbd)',
        yaxis=dict(
            range=[y_min, y_max],
            tickformat=',.0f'
        ),
        template='plotly_white',
        height=500,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return dcc.Graph(figure=fig)

def create_trend_analysis(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    # Calculate different moving averages
    ma_3 = monthly.rolling(window=3, center=True).mean()
    ma_6 = monthly.rolling(window=6, center=True).mean()
    ma_12 = monthly.rolling(window=12, center=True).mean()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines',
        name='Actual',
        line=dict(color='lightgray', width=1),
        opacity=0.6
    ))
    
    fig.add_trace(go.Scatter(
        x=ma_3.index,
        y=ma_3.values,
        mode='lines',
        name='3-Month MA',
        line=dict(color='#2E86AB', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=ma_6.index,
        y=ma_6.values,
        mode='lines',
        name='6-Month MA',
        line=dict(color='#A23B72', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=ma_12.index,
        y=ma_12.values,
        mode='lines',
        name='12-Month MA',
        line=dict(color='#F18F01', width=2)
    ))
    
    fig.update_layout(
        title='Moving Average Trend Analysis',
        xaxis_title='Date',
        yaxis_title='Volume (kbd)',
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_yoy_comparison(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    current_year = datetime.now().year
    years = [current_year - 2, current_year - 1, current_year]
    
    fig = go.Figure()
    
    for year in years:
        year_data = filtered_processor.df[filtered_processor.df['RPT_PERIOD'].dt.year == year]
        monthly = year_data.groupby(year_data['RPT_PERIOD'].dt.month)['QUANTITY'].sum()
        
        fig.add_trace(go.Scatter(
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=[monthly.get(i, 0) for i in range(1, 13)],
            mode='lines+markers',
            name=str(year),
            line=dict(width=2),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title='Year-over-Year Comparison',
        xaxis_title='Month',
        yaxis_title='Volume (kbd)',
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def create_volatility_analysis(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    # Calculate rolling volatility (standard deviation)
    rolling_std = monthly.rolling(window=12).std()
    pct_change = monthly.pct_change() * 100
    
    fig = go.Figure()
    
    # Create subplot with secondary y-axis
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines',
        name='Volume',
        yaxis='y',
        line=dict(color='#2E86AB', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=rolling_std.index,
        y=rolling_std.values,
        mode='lines',
        name='12-Month Rolling Volatility',
        yaxis='y2',
        line=dict(color='#A23B72', width=2)
    ))
    
    fig.update_layout(
        title='Volume and Volatility Analysis',
        xaxis_title='Date',
        yaxis=dict(title='Volume (kbd)', side='left'),
        yaxis2=dict(title='Volatility (Std Dev)', overlaying='y', side='right'),
        template='plotly_white',
        height=450,
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig)

def generate_forecast_metrics_table(padd_filter='US'):
    filtered_processor = CLIDataProcessor()
    if padd_filter != 'US':
        padd_num = int(padd_filter.replace('PADD ', ''))
        filtered_processor.df = filtered_processor.df[filtered_processor.df['PORT_PADD'] == padd_num]
    else:
        filtered_processor = processor
    
    monthly = filtered_processor.df.groupby('RPT_PERIOD')['QUANTITY'].sum()
    
    # Calculate various metrics
    current_month = monthly.iloc[-1]
    prev_month = monthly.iloc[-2]
    year_ago = monthly.iloc[-12] if len(monthly) > 12 else monthly.iloc[0]
    
    mom_change = ((current_month - prev_month) / prev_month * 100)
    yoy_change = ((current_month - year_ago) / year_ago * 100)
    
    # Calculate trend strength (R-squared of linear regression)
    X = np.arange(len(monthly[-12:])).reshape(-1, 1)
    y = monthly[-12:].values
    model = LinearRegression()
    model.fit(X, y)
    trend_strength = model.score(X, y) * 100
    
    # Calculate seasonal strength
    try:
        decomposition = seasonal_decompose(monthly[-36:], model='additive', period=12)
        seasonal_strength = (decomposition.seasonal.std() / monthly[-36:].std() * 100)
    except:
        seasonal_strength = 0
    
    data = [
        {'Metric': 'Current Month Volume', 'Value': f'{current_month:,.1f} kbd'},
        {'Metric': 'Month-over-Month Change', 'Value': f'{mom_change:+.1f}%'},
        {'Metric': 'Year-over-Year Change', 'Value': f'{yoy_change:+.1f}%'},
        {'Metric': '12-Month Average', 'Value': f'{monthly[-12:].mean():,.1f} kbd'},
        {'Metric': '12-Month Volatility', 'Value': f'{monthly[-12:].std():,.1f} kbd'},
        {'Metric': 'Trend Strength (R²)', 'Value': f'{trend_strength:.1f}%'},
        {'Metric': 'Seasonal Strength', 'Value': f'{seasonal_strength:.1f}%'},
        {'Metric': 'Forecast Confidence', 'Value': 'High' if trend_strength > 70 else 'Medium' if trend_strength > 40 else 'Low'}
    ]
    
    return dash_table.DataTable(
        data=data,
        columns=[
            {"name": "Metric", "id": "Metric"},
            {"name": "Value", "id": "Value"}
        ],
        style_table={'border': 'none', 'borderRadius': '15px',
                    'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'},
        style_cell={'textAlign': 'left', 'padding': '10px',
                   'fontFamily': 'Arial', 'fontSize': '12px'},
        style_header={'backgroundColor': '#bfbec4', 'color': 'black',
                     'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{Value} contains "+"'},
                'backgroundColor': 'lightgreen',
                'color': 'green'
            },
            {
                'if': {'filter_query': '{Value} contains "-" and {Value} != "-"'},
                'backgroundColor': 'lightpink',
                'color': '#c00000'
            },
            {
                'if': {'filter_query': '{Value} = "High"'},
                'backgroundColor': 'lightgreen',
                'color': 'green'
            },
            {
                'if': {'filter_query': '{Value} = "Low"'},
                'backgroundColor': 'lightpink',
                'color': '#c00000'
            }
        ]
    )

layout = html.Div([
    html.Div([
        html.H1('EIA CLI - Advanced Time Series Forecasting',
                style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # PADD Filter Dropdown
        html.Div([
            html.Label('Filter by PADD:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='padd-filter-forecast',
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
                html.H3('Forecast Metrics', style={'marginBottom': '20px'}),
                html.Div(id='forecast-metrics-table')
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Div(id='arima-forecast-chart')
            ], style={'width': '68%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '40px'}),
        
        html.Hr(),
        
        html.Div([
            html.Div(id='trend-analysis-chart',
                    style={'width': '48%', 'display': 'inline-block'}),
            html.Div(id='yoy-comparison-chart',
                    style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([
            html.Div(id='volatility-analysis-chart',
                    style={'width': '100%'})
        ], style={'marginBottom': '30px'})
        
    ], style={'padding': '20px', 'maxWidth': '1600px', 'margin': 'auto'})
])

# Callbacks for PADD filtering
@callback(
    [Output('forecast-metrics-table', 'children'),
     Output('arima-forecast-chart', 'children'),
     Output('trend-analysis-chart', 'children'),
     Output('yoy-comparison-chart', 'children'),
     Output('volatility-analysis-chart', 'children')],
    Input('padd-filter-forecast', 'value')
)
def update_forecast_charts(padd_filter):
    return (
        generate_forecast_metrics_table(padd_filter),
        create_arima_forecast(padd_filter),
        create_trend_analysis(padd_filter),
        create_yoy_comparison(padd_filter),
        create_volatility_analysis(padd_filter)
    )