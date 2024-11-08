from dash import html, dcc, callback, Output, Input

# Page layout for a blank holding page
layout = html.Div([
    html.H1("Page Under Construction", style={"fontSize": "3em", "color": "#c00000", "textAlign": "center"}),
    html.P("This page is currently being developed. Please check back later.", 
           style={"fontSize": "1.5em", "color": "#666", "textAlign": "center", "marginTop": "20px"})
], style={"height": "100vh", "display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center"})