import dash
from dash import html
import dash_ag_grid as dag
import pandas as pd
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Sample data setup
meta_columns = ['Meta1', 'Meta2', 'Meta3']
month_columns = pd.date_range('2024-01', '2024-12', freq='ME').strftime('%Y-%m').tolist()
columns = meta_columns + month_columns
data = []

for _ in range(20):
    row = {col: np.random.randint(1, 100) for col in columns}
    data.append(row)
data.append({col: None for col in columns})
for _ in range(30):
    row = {col: np.random.randint(1, 100) for col in columns}
    data.append(row)
data.append({col: None for col in columns})
bold_row = {col: np.random.randint(1, 100) for col in columns}
bold_row['bold'] = True
data.append(bold_row)

df = pd.DataFrame(data)

# Define column definitions
column_defs = [
    {'headerName': col, 'field': col, 'pinned': 'left' if col in meta_columns else None}
    for col in columns
]

# Define Ag-Grid component with custom styling
grid = dag.AgGrid(
    columnDefs=column_defs,
    rowData=df.to_dict('records'),
    defaultColDef={
        "sortable": True,
        "filter": True,
    },
    getRowStyle={
        'function': """params => params.data.bold ? { fontWeight: 'bold', color: 'black' } : { color: 'black' }"""
    },
    className="ag-theme-alpine-dark",  # Match this with your custom CSS class
    style={'height': '100%', 'width': '100%'}  # Fill the available space
)

# Define the layout
app.layout = html.Div(
    [
        html.H2("Dash Ag-Grid Example with Custom Theme Colors"),
        grid
    ],
    style={'height': '100vh', 'display': 'flex', 'flexDirection': 'column'}
)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)