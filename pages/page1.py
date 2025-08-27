import pandas as pd
import numpy as np
from dash import dcc, html, callback, Input, Output, State, clientside_callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def create_metric_card(title, value, change, icon, color):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.I(className=f"fas {icon} fa-2x", style={"color": color, "opacity": "0.8"}),
                ], width=3),
                dbc.Col([
                    html.H6(title, className="text-muted", style={"fontSize": "0.85rem", "fontWeight": "600", "letterSpacing": "0.5px"}),
                    html.H3(value, style={"fontWeight": "700", "marginBottom": "0.25rem"}),
                    html.Div([
                        html.Span(
                            f"{change}",
                            style={
                                "color": "#10b759" if "+" in change else "#dc3545",
                                "fontSize": "0.9rem",
                                "fontWeight": "600"
                            }
                        ),
                        html.Span(" vs last week", style={"fontSize": "0.8rem", "color": "#6c757d", "marginLeft": "4px"})
                    ])
                ], width=9)
            ])
        ])
    ], style={
        "boxShadow": "0 2px 15px rgba(0,0,0,0.08)",
        "borderRadius": "12px",
        "border": "none",
        "backgroundColor": "white",
        "height": "120px",
        "transition": "transform 0.2s, box-shadow 0.2s",
    }, className="metric-card mb-4")

def create_section_card(title, description, icon, link, color):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"fas {icon} fa-3x", style={"color": color, "marginBottom": "1rem"}),
                ], style={"textAlign": "center"}),
                html.H5(title, style={"fontWeight": "700", "marginBottom": "0.75rem", "minHeight": "32px"}),
                html.P(description, style={"fontSize": "0.9rem", "color": "#6c757d", "marginBottom": "1.25rem", "lineHeight": "1.6", "minHeight": "72px"}),
                dbc.Button(
                    "Explore",
                    href=link,
                    color="primary",
                    outline=True,
                    size="sm",
                    style={
                        "borderRadius": "6px",
                        "fontWeight": "600",
                        "letterSpacing": "0.3px",
                        "borderColor": color,
                        "color": color
                    },
                    className="section-explore-btn"
                )
            ], style={"display": "flex", "flexDirection": "column", "height": "100%"}),
        ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
    ], style={
        "boxShadow": "0 3px 20px rgba(0,0,0,0.1)",
        "borderRadius": "15px",
        "border": "none",
        "height": "100%",
        "backgroundColor": "white",
        "transition": "transform 0.3s, box-shadow 0.3s",
    }, className="section-card h-100")

def create_mini_chart():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    values = [random.uniform(80, 100) for _ in range(30)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines',
        line=dict(color='#e97132', width=2),
        fill='tozeroy',
        fillcolor='rgba(233, 113, 50, 0.1)',
        showlegend=False
    ))
    
    fig.update_layout(
        height=60,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        hovermode=False
    )
    
    return fig

layout = html.Div([
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    dcc.Store(id='metrics-data-store'),
    
    # Div to inject dynamic CSS (not hidden so CSS takes effect)
    html.Div(id='font-css', children=[]),
    
    # Font Selector at top of page
    html.Div([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Typography Settings", style={"fontWeight": "700", "marginBottom": "0.5rem", "fontSize": "0.9rem", "color": "#2c3e50"}),
                        html.Div([
                            html.Label("Select Font: ", style={"marginRight": "10px", "fontSize": "0.85rem", "color": "#6c757d"}),
                            dcc.Dropdown(
                                id='font-selector',
                                options=[
                                    {'label': 'Montserrat (Goldman Sans style)', 'value': 'Montserrat'},
                                    {'label': 'Inter (Modern & Clean)', 'value': 'Inter'},
                                    {'label': 'Source Sans Pro (Adobe)', 'value': 'Source Sans Pro'},
                                    {'label': 'Open Sans (Classic)', 'value': 'Open Sans'},
                                    {'label': 'IBM Plex Sans (Technical)', 'value': 'IBM Plex Sans'},
                                    {'label': 'Work Sans (Industrial)', 'value': 'Work Sans'},
                                    {'label': 'Barlow (Condensed)', 'value': 'Barlow'},
                                    {'label': 'Nunito Sans (Friendly)', 'value': 'Nunito Sans'},
                                    {'label': 'Roboto (Google)', 'value': 'Roboto'},
                                ],
                                value='Montserrat',
                                clearable=False,
                                style={"width": "300px", "fontSize": "0.9rem"},
                                className="font-selector-dropdown"
                            ),
                        ], style={"display": "flex", "alignItems": "center"}),
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.P("Preview: ", style={"fontSize": "0.85rem", "color": "#6c757d", "marginBottom": "0.25rem"}),
                            html.Div([
                                html.Span("Aa Bb Cc 123", id="font-preview", style={"fontSize": "1.5rem", "fontWeight": "500"}),
                            ])
                        ])
                    ], width=6, style={"textAlign": "right"})
                ])
            ])
        ], style={
            "boxShadow": "0 2px 10px rgba(0,0,0,0.05)",
            "borderRadius": "10px",
            "marginBottom": "2rem",
            "border": "1px solid #e9ecef"
        })
    ]),
    
    # Hero Section
    html.Div([
        html.Div([
            html.H1(
                "Energy Intelligence Dashboard",
                style={
                    "fontSize": "3rem",
                    "fontWeight": "800",
                    "color": "#2c3e50",
                    "marginBottom": "0.5rem",
                    "letterSpacing": "-1px"
                }
            ),
            html.P(
                "Real-time analysis and visualization of U.S. energy markets",
                style={
                    "fontSize": "1.25rem",
                    "color": "#6c757d",
                    "fontWeight": "400",
                    "marginBottom": "2rem"
                }
            ),
            html.Div([
                dbc.Button(
                    ["Get Started ", html.I(className="fas fa-arrow-right ms-2")],
                    href="/stats/headline",
                    color="danger",
                    size="lg",
                    style={
                        "borderRadius": "8px",
                        "fontWeight": "600",
                        "padding": "0.75rem 2rem",
                        "boxShadow": "0 4px 15px rgba(192, 0, 0, 0.3)",
                        "backgroundColor": "#c00000",
                        "border": "none"
                    }
                ),
                dbc.Button(
                    ["View Documentation ", html.I(className="fas fa-book ms-2")],
                    color="light",
                    size="lg",
                    style={
                        "borderRadius": "8px",
                        "fontWeight": "600",
                        "padding": "0.75rem 2rem",
                        "marginLeft": "1rem",
                        "border": "1px solid #dee2e6"
                    }
                ),
            ])
        ], style={"textAlign": "center", "padding": "4rem 0"}),
    ], style={
        "background": "linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%)",
        "borderRadius": "20px",
        "marginBottom": "3rem",
        "boxShadow": "0 10px 40px rgba(0,0,0,0.05)"
    }),
    
    # Key Metrics Section
    html.Div([
        html.H3("Key Metrics", style={
            "fontWeight": "700",
            "marginBottom": "1.5rem",
            "color": "#2c3e50",
            "fontSize": "1.75rem"
        }),
        dbc.Row(id='metrics-row'),
    ], style={"marginBottom": "3rem"}),
    
    # Dashboard Sections
    html.Div([
        html.H3("Dashboard Sections", style={
            "fontWeight": "700",
            "marginBottom": "1.5rem",
            "color": "#2c3e50",
            "fontSize": "1.75rem"
        }),
        dbc.Row([
            dbc.Col([
                create_section_card(
                    "Weekly Statistics",
                    "Comprehensive analysis of weekly petroleum supply data including stocks, production, and imports.",
                    "fa-chart-line",
                    "/stats/headline",
                    "#e97132"
                )
            ], lg=3, md=6, className="mb-4"),
            dbc.Col([
                create_section_card(
                    "Drilling Productivity",
                    "Regional drilling productivity reports, efficiency metrics, and DUC inventory analysis.",
                    "fa-hard-hat",
                    "/dpr/dpr_charts",
                    "#3498db"
                )
            ], lg=3, md=6, className="mb-4"),
            dbc.Col([
                create_section_card(
                    "STEO Outlook",
                    "Short-term energy outlook with forecasts, market trends, and supply/demand projections.",
                    "fa-chart-area",
                    "/steo/steo_1",
                    "#27ae60"
                )
            ], lg=3, md=6, className="mb-4"),
            dbc.Col([
                create_section_card(
                    "Company Imports",
                    "Company-level crude oil imports data, analysis tools, and historical trends.",
                    "fa-ship",
                    "/cli/cli_overview",
                    "#8e44ad"
                )
            ], lg=3, md=6, className="mb-4"),
        ])
    ], style={"marginBottom": "3rem"}),
    
    # Trending Analysis Section
    html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Market Activity", style={"fontWeight": "700", "marginBottom": "1rem"}),
                        html.Div([
                            dcc.Graph(
                                id='mini-chart',
                                config={'displayModeBar': False},
                                style={"marginBottom": "1rem"}
                            ),
                            html.Div([
                                html.Span("Crude Oil Price Trend", style={"fontSize": "0.9rem", "color": "#6c757d"}),
                                html.Span(" | ", style={"margin": "0 0.5rem", "color": "#dee2e6"}),
                                html.Span("Last 30 Days", style={"fontSize": "0.85rem", "color": "#6c757d"})
                            ])
                        ])
                    ])
                ], style={
                    "boxShadow": "0 3px 15px rgba(0,0,0,0.08)",
                    "borderRadius": "12px",
                    "border": "none",
                    "height": "100%"
                })
            ], lg=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Quick Links", style={"fontWeight": "700", "marginBottom": "1.25rem"}),
                        html.Div([
                            html.A([
                                html.I(className="fas fa-external-link-alt me-2"),
                                "EIA Weekly Report"
                            ], href="#", className="d-block mb-3", style={"color": "#e97132", "textDecoration": "none", "fontSize": "0.95rem"}),
                            html.A([
                                html.I(className="fas fa-external-link-alt me-2"),
                                "STEO Full Report"
                            ], href="#", className="d-block mb-3", style={"color": "#e97132", "textDecoration": "none", "fontSize": "0.95rem"}),
                            html.A([
                                html.I(className="fas fa-external-link-alt me-2"),
                                "API Documentation"
                            ], href="#", className="d-block mb-3", style={"color": "#e97132", "textDecoration": "none", "fontSize": "0.95rem"}),
                            html.A([
                                html.I(className="fas fa-external-link-alt me-2"),
                                "Data Sources"
                            ], href="#", className="d-block", style={"color": "#e97132", "textDecoration": "none", "fontSize": "0.95rem"}),
                        ])
                    ])
                ], style={
                    "boxShadow": "0 3px 15px rgba(0,0,0,0.08)",
                    "borderRadius": "12px",
                    "border": "none",
                    "height": "100%"
                })
            ], lg=4)
        ])
    ], style={"marginBottom": "3rem"}),
    
    # Status Bar
    html.Div([
        html.Hr(style={"borderColor": "#dee2e6", "opacity": "0.3"}),
        html.Div([
            html.Span([
                html.I(className="fas fa-circle me-2", style={"color": "#10b759", "fontSize": "0.5rem"}),
                "All Systems Operational"
            ], style={"color": "#6c757d", "fontSize": "0.9rem"}),
            html.Span(" | ", style={"margin": "0 1rem", "color": "#dee2e6"}),
            html.Span([
                "Last Updated: ",
                html.Span(id="last-updated", children=datetime.now().strftime("%B %d, %Y at %I:%M %p"))
            ], style={"color": "#6c757d", "fontSize": "0.9rem"})
        ], style={"textAlign": "center", "padding": "1rem 0"})
    ])
], style={
    "padding": "2rem",
    "backgroundColor": "#f4f5f9",
    "minHeight": "100vh"
})

@callback(
    Output('last-updated', 'children'),
    Output('mini-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_dashboard_data(n):
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    chart_figure = create_mini_chart()
    return timestamp, chart_figure

# Clientside callback for font switching
clientside_callback(
    """
    function(selectedFont) {
        if (!selectedFont) {
            return [{}, ''];
        }
        
        // Remove existing style if any
        var existingStyle = document.getElementById('dynamic-font-style');
        if (existingStyle) {
            existingStyle.remove();
        }
        
        // Create new style element
        var style = document.createElement('style');
        style.id = 'dynamic-font-style';
        style.innerHTML = `
            * {
                font-family: '${selectedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            }
            
            body {
                font-family: '${selectedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            }
            
            h1, h2, h3, h4, h5, h6, p, a, div, span, button, input, textarea, td, th, li {
                font-family: '${selectedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            }
            
            .nav-link, .btn, .card, .sidebar {
                font-family: '${selectedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            }
        `;
        document.head.appendChild(style);
        
        // Update preview style
        var previewStyle = {
            'fontSize': '1.5rem',
            'fontWeight': '500',
            'fontFamily': `'${selectedFont}', sans-serif`
        };
        
        // Store preference
        localStorage.setItem('selectedFont', selectedFont);
        
        console.log('Font changed to:', selectedFont);
        
        return [previewStyle, ''];
    }
    """,
    [Output('font-preview', 'style'),
     Output('font-css', 'children')],
    Input('font-selector', 'value')
)

# Callback to load and display real metrics data
@callback(
    Output('metrics-row', 'children'),
    Output('metrics-data-store', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_metrics(n):
    try:
        # Load the latest data
        df = pd.read_feather('./data/wps/wps_gte_2015_pivot.feather')
        
        # Get the latest two periods for comparison
        df['period'] = pd.to_datetime(df['period'])
        df_sorted = df.sort_values('period')
        latest = df_sorted.iloc[-1]
        previous = df_sorted.iloc[-2]
        
        # Extract key metrics (converting from kb to Mb)
        metrics = {
            'crude': {
                'current': latest.get('WCESTUS1', 0) / 1000,  # Convert kb to Mb
                'previous': previous.get('WCESTUS1', 0) / 1000,
                'title': 'CRUDE OIL STOCKS',
                'icon': 'fa-oil-can',
                'color': '#e97132'
            },
            'gasoline': {
                'current': latest.get('WGTSTUS1', 0) / 1000,
                'previous': previous.get('WGTSTUS1', 0) / 1000,
                'title': 'GASOLINE STOCKS', 
                'icon': 'fa-gas-pump',
                'color': '#3498db'
            },
            'distillate': {
                'current': latest.get('WDISTUS1', 0) / 1000,
                'previous': previous.get('WDISTUS1', 0) / 1000,
                'title': 'DISTILLATE FUEL',
                'icon': 'fa-truck',
                'color': '#27ae60'
            },
            'refinery': {
                'current': latest.get('WPULEUS3', 0),  # Refinery utilization %
                'previous': previous.get('WPULEUS3', 0),
                'title': 'REFINERY UTIL.',
                'icon': 'fa-industry',
                'color': '#8e44ad'
            }
        }
        
        # Create metric cards with real data
        cards = []
        for key, data in metrics.items():
            change = data['current'] - data['previous']
            
            if key == 'refinery':
                # Format as percentage
                value_str = f"{data['current']:.1f}%"
                change_str = f"{'+' if change >= 0 else ''}{change:.1f}%"
            else:
                # Format as Mb
                value_str = f"{data['current']:.1f}M"
                change_str = f"{'+' if change >= 0 else ''}{change:.1f}M"
            
            cards.append(
                dbc.Col([
                    create_metric_card(
                        data['title'],
                        value_str,
                        change_str,
                        data['icon'],
                        data['color']
                    )
                ], lg=3, md=6)
            )
        
        return cards, metrics
        
    except Exception as e:
        # Fallback to placeholder data if there's an error
        print(f"Error loading metrics: {e}")
        default_cards = [
            dbc.Col([
                create_metric_card(
                    "CRUDE OIL STOCKS",
                    "Loading...",
                    "--",
                    "fa-oil-can",
                    "#e97132"
                )
            ], lg=3, md=6),
            dbc.Col([
                create_metric_card(
                    "GASOLINE STOCKS",
                    "Loading...",
                    "--",
                    "fa-gas-pump",
                    "#3498db"
                )
            ], lg=3, md=6),
            dbc.Col([
                create_metric_card(
                    "DISTILLATE FUEL",
                    "Loading...",
                    "--",
                    "fa-truck",
                    "#27ae60"
                )
            ], lg=3, md=6),
            dbc.Col([
                create_metric_card(
                    "REFINERY UTIL.",
                    "Loading...",
                    "--",
                    "fa-industry",
                    "#8e44ad"
                )
            ], lg=3, md=6),
        ]
        return default_cards, {}
