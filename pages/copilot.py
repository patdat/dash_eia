import dash
from dash import dcc,html
import pandas as pd

# Load the data from the feather file
data = pd.read_feather('./data/wps_gte_2015_pivot.feather')

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("Ag Grid Dash App"),
    dcc.Graph(
        id='ag-grid',
        figure={
            'data': [
                {
                    'type': 'heatmap',
                    'z': data.values.tolist(),
                    'x': data.columns.tolist(),
                    'y': data.index.tolist(),
                    'colorscale': 'Viridis'
                }
            ],
            'layout': {
                'title': 'Heatmap of Data'
            }
        }
    )
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)