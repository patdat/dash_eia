from dash import Dash, dcc, html, callback, Input, Output
from app import app
import pages.page1, pages.page2

# Setup the app layout with navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Nav([
        dcc.Link('Page 1', href='/page1', style={'margin-right': '10px'}),
        dcc.Link('Page 2', href='/page2')
    ]),
    html.Div(id='page-content')
])

# Callback to control page rendering based on navigation
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/page1':
        return pages.page1.layout
    elif pathname == '/page2':
        return pages.page2.layout
    else:
        return html.Div([
            html.H1('404 Error'),
            html.P('No page found at this location.')
        ])

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
