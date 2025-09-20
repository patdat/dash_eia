from dash import Dash
import dash_bootstrap_components as dbc
import pandas as pd

app = Dash(__name__, suppress_callback_exceptions=True,
           external_stylesheets=[
               dbc.themes.BOOTSTRAP,
               # Add Google Fonts directly
               'https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap',
               'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
               'https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700;900&display=swap',
               'https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap',
               'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap',
               'https://fonts.googleapis.com/css2?family=Work+Sans:wght@300;400;500;600;700&display=swap',
               'https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&display=swap',
               'https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800&display=swap',
               'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap'
           ])
server = app.server

def load_data():
    """Load initial data with caching fallback"""
    try:
        # Try to load from cached data loader first
        from src.utils.data_loader import cached_loader
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