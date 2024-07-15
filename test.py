import dash
import dash_ag_grid as dag
from dash import html, Output, Input

app = dash.Dash(__name__)

app.layout = html.Div([
    dag.AgGrid(
        id='ag-grid',
        columnDefs=[
            {'headerName': 'Column 1', 'field': 'col1', 'cellStyle': {'backgroundColor': 'white', '--hover-background-color': 'lightblue'}},
            {'headerName': 'Column 2', 'field': 'col2', 'cellStyle': {'backgroundColor': 'white', '--hover-background-color': 'lightblue'}},
            {'headerName': 'Column 3', 'field': 'col3', 'cellStyle': {'backgroundColor': 'white', '--hover-background-color': 'lightblue'}},
            {'headerName': 'Column 4', 'field': 'col4', 'cellStyle': {'backgroundColor': 'white', '--hover-background-color': 'lightblue'}},
            {'headerName': 'Column 5', 'field': 'col5', 'cellStyle': {'backgroundColor': 'white', '--hover-background-color': 'lightblue'}}
        ],
        rowData=[
            {'col1': 'Row 1 Col 1', 'col2': 'Row 1 Col 2', 'col3': 'Row 1 Col 3', 'col4': 'Row 1 Col 4', 'col5': 'Row 1 Col 5'},
            {'col1': 'Row 2 Col 1', 'col2': 'Row 2 Col 2', 'col3': 'Row 2 Col 3', 'col4': 'Row 2 Col 4', 'col5': 'Row 2 Col 5'},
            {'col1': 'Row 3 Col 1', 'col2': 'Row 3 Col 2', 'col3': 'Row 3 Col 3', 'col4': 'Row 3 Col 4', 'col5': 'Row 3 Col 5'},
            {'col1': 'Row 4 Col 1', 'col2': 'Row 4 Col 2', 'col3': 'Row 4 Col 3', 'col4': 'Row 4 Col 4', 'col5': 'Row 4 Col 5'},
            {'col1': 'Row 5 Col 1', 'col2': 'Row 5 Col 2', 'col3': 'Row 5 Col 3', 'col4': 'Row 5 Col 4', 'col5': 'Row 5 Col 5'}
        ]
    )
])

@app.callback(
    Output('ag-grid', 'style'),
    Input('ag-grid', 'hoverRowIndex')
)
def update_style_hoverRowIndex(row):
    if row is not None:
        return {'--hover-background-color': 'lightblue'}
    return {}

if __name__ == '__main__':
    app.run_server(debug=True)
