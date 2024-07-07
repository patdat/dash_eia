import dash
from utils.mapping import production_mapping
from utils.download import main as download_raw_file
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output

from app import app
import pandas as pd

initial_data = pd.read_csv('./data/wps_gte_2015_pivot.csv').to_dict('records')

layout = html.Div([
    html.Button('Generate and Save Data', id='generate-data-btn'),
    dash_table.DataTable(id='data-table')  # Table to display data
])

@app.callback(
    Output('data-store', 'data'),
    Input('generate-data-btn', 'n_clicks'),
    prevent_initial_call=True
)
def generate_data(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        df = download_raw_file()
        return df.to_dict('records')
    else:
        df = pd.DataFrame(initial_data)
    return df.to_dict('records')

@app.callback(
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('data-store', 'data')
)
def update_table(data):
    if data is None:
        return dash.no_update, dash.no_update
    df = pd.DataFrame(data)
    print("Data updated in table in page2_1:", df.head())  # Debugging statement
    df_sliced = df.iloc[-5:, :5]
    data_sliced = df_sliced.to_dict('records')
    columns = [{"name": col, "id": col} for col in df_sliced.columns]
    return data_sliced, columns
