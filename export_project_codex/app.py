from dash import Dash
import dash_bootstrap_components as dbc


EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap",
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    "https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700;900&display=swap",
    "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap",
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap",
    "https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&display=swap",
]


app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=EXTERNAL_STYLESHEETS,
)
server = app.server
