"""
Cache management utilities for the Dash app
"""
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
from utils.data_loader import cached_loader, get_cache_stats, refresh_data_and_cache, invalidate_data_cache, check_data_freshness
from utils.cache import app_cache
import pandas as pd

def create_cache_management_layout():
    """Create a cache management interface"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Cache Management", className="text-center mb-4"),
                
                # Cache stats
                dbc.Card([
                    dbc.CardHeader(html.H4("Cache Statistics")),
                    dbc.CardBody([
                        html.Div(id="cache-stats-display"),
                        dbc.Button("Refresh Stats", id="refresh-stats-btn", color="primary", className="mt-2")
                    ])
                ], className="mb-4"),
                
                # Data freshness check
                dbc.Card([
                    dbc.CardHeader(html.H4("Data Freshness")),
                    dbc.CardBody([
                        html.Div(id="data-freshness-display"),
                        dbc.Button("Check Data Files", id="check-freshness-btn", color="info", className="mt-2")
                    ])
                ], className="mb-4"),
                
                # Cache operations
                dbc.Card([
                    dbc.CardHeader(html.H4("Cache Operations")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Clear All Cache", id="clear-cache-btn", color="warning", className="me-2"),
                                dbc.Button("Preload Data", id="preload-btn", color="success", className="me-2"),
                                dbc.Button("Refresh Data & Cache", id="refresh-data-btn", color="primary", className="me-2"),
                                dbc.Button("Invalidate WPS Cache", id="invalidate-wps-btn", color="secondary")
                            ])
                        ]),
                        html.Hr(),
                        html.Div(id="cache-operation-result", className="mt-2")
                    ])
                ])
            ])
        ])
    ], fluid=True)


@callback(
    Output("cache-stats-display", "children"),
    [Input("refresh-stats-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_cache_stats(n_clicks):
    """Update cache statistics display"""
    try:
        stats = get_cache_stats()
        
        stats_content = [
            html.P(f"Total cached items: {stats['total_cached_items']}"),
            html.H6("Cached Keys:"),
            html.Ul([
                html.Li(key) for key in stats['cache_keys'][:10]  # Show first 10 keys
            ]),
        ]
        
        if stats['total_cached_items'] > 10:
            stats_content.append(html.P(f"... and {stats['total_cached_items'] - 10} more"))
        
        return stats_content
        
    except Exception as e:
        return html.P(f"Error loading cache stats: {str(e)}", className="text-danger")


@callback(
    Output("data-freshness-display", "children"),
    [Input("check-freshness-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_data_freshness(n_clicks):
    """Update data freshness display"""
    try:
        file_info = check_data_freshness()
        
        freshness_content = []
        for file_path, info in file_info.items():
            file_name = file_path.split('/')[-1]  # Get just the filename
            if info['exists']:
                badge_color = "success"
                status = f"✅ {file_name}"
                detail = f"Modified: {info['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                badge_color = "danger"
                status = f"❌ {file_name}"
                detail = "File not found"
            
            freshness_content.append(
                html.Div([
                    dbc.Badge(status, color=badge_color, className="me-2"),
                    html.Small(detail, className="text-muted")
                ], className="mb-2")
            )
        
        return freshness_content
        
    except Exception as e:
        return html.P(f"Error checking data freshness: {str(e)}", className="text-danger")


@callback(
    Output("cache-operation-result", "children"),
    [
        Input("clear-cache-btn", "n_clicks"),
        Input("preload-btn", "n_clicks"),
        Input("refresh-data-btn", "n_clicks"),
        Input("invalidate-wps-btn", "n_clicks")
    ],
    prevent_initial_call=True
)
def handle_cache_operations(clear_clicks, preload_clicks, refresh_clicks, invalidate_clicks):
    """Handle cache operation button clicks"""
    import dash
    from utils.data_loader import preload_common_data
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "clear-cache-btn":
            invalidate_data_cache()
            return dbc.Alert("All cache cleared successfully!", color="success", dismissable=True)
        
        elif button_id == "preload-btn":
            preload_common_data()
            return dbc.Alert("Data preloaded successfully!", color="success", dismissable=True)
        
        elif button_id == "refresh-data-btn":
            refresh_data_and_cache()
            return dbc.Alert("Data and cache refreshed successfully! All data has been reloaded from disk.", color="success", dismissable=True)
        
        elif button_id == "invalidate-wps-btn":
            cached_loader.invalidate_cache("wps")
            return dbc.Alert("WPS cache invalidated successfully!", color="info", dismissable=True)
    
    except Exception as e:
        return dbc.Alert(f"Operation failed: {str(e)}", color="danger", dismissable=True)
    
    return ""


# Layout for cache management page
cache_management_layout = create_cache_management_layout()
