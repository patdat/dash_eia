from dash import Dash
import dash_bootstrap_components as dbc
import pandas as pd

app = Dash(__name__, suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

def load_data():
    """Load initial data with caching fallback"""
    try:
        # Try to load from cached data loader first
        from utils.data_loader import cached_loader
        df = cached_loader.load_wps_pivot_data()
        return df.to_dict('records')
    except Exception as e:
        print(f"Failed to load cached data: {e}")
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