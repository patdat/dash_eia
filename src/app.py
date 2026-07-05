import os
from dash import Dash
import dash_bootstrap_components as dbc
import pandas as pd

# Project root is one level up from src/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Dash(__name__, suppress_callback_exceptions=True,
           assets_folder=os.path.join(PROJECT_ROOT, 'assets'),
           external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

def load_data():
    """Load initial data"""
    try:
        from src.utils.data_loader import loader
        df = loader.load_wps_pivot_data()
        return df.to_dict('records')
    except Exception as e:
        print(f"Failed to load data: {e}")
        # Fallback to direct file loading
        try:
            return pd.read_feather('./data/wps/wps_gte_2015_pivot.feather').to_dict('records')
        except:
            try:
                return pd.read_csv('./data/wps/wps_gte_2015_pivot.csv').to_dict('records')
            except FileNotFoundError:
                return []

# Load the data into a variable
initial_data = load_data()