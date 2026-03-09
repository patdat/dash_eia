from dash import Input, Output, State, MATCH, dcc, html
from dash.exceptions import PreventUpdate

from app import app
from components.shell import build_sidebar
from config.navigation import BRAND, NAV_SECTIONS, PAGE_CONTENT
from pages.home import build_home_page
from pages.placeholder import build_placeholder_page


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        build_sidebar(BRAND, NAV_SECTIONS),
        html.Main(id="page-content", className="content-area"),
    ]
)


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    page = PAGE_CONTENT.get(pathname, PAGE_CONTENT["/"])
    if pathname == "/":
        return build_home_page()
    return build_placeholder_page(page)


@app.callback(
    Output({"type": "nav-collapse", "index": MATCH}, "is_open"),
    Output({"type": "nav-toggle", "index": MATCH}, "className"),
    Input({"type": "nav-toggle", "index": MATCH}, "n_clicks"),
    State({"type": "nav-collapse", "index": MATCH}, "is_open"),
    State({"type": "nav-toggle", "index": MATCH}, "className"),
    prevent_initial_call=True,
)
def toggle_section(n_clicks, is_open, class_name):
    if not n_clicks:
        raise PreventUpdate

    next_open = not is_open
    if next_open:
        return next_open, class_name.replace("closed", "open")
    return next_open, class_name.replace("open", "closed")


if __name__ == "__main__":
    app.run(debug=True, port=8050)
