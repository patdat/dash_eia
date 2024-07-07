from dash import Dash
import dash_bootstrap_components as dbc
import pandas as pd

app = Dash(__name__, suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

def load_data():
    try:
        return pd.read_csv('./data/wps_gte_2015_pivot.csv').to_dict('records')
    except FileNotFoundError:
        return []

# Load the data into a variable
initial_data = load_data()