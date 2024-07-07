import dash
from dash import Output, Input
import pandas as pd
from utils.graph_seag import chart_seasonality
from utils.graph_line import chart_trend
from utils.mapping import production_mapping

def get_initial_data():
    df = pd.read_csv('./data/wps_gte_2015_pivot.csv', parse_dates=['period'])
    df = df[df['period'] > '2015-01-01']
    return df

def get_data(df, id):
    filtered_df = df[['period', id]]
    filtered_df = filtered_df.rename(columns={id: 'value'})
    mapping_name = production_mapping.get(id)
    stocks_in_name = 'stocks' in mapping_name.lower()
    mapping_name = mapping_name.replace('(kbd)', '(kb/d)')

    if stocks_in_name:
        filtered_df['value'] = filtered_df['value'] / 1000
        mapping_name = mapping_name.replace('(kb)', '(mb)').lower().replace('thousands', 'Millions')

    return filtered_df, mapping_name, stocks_in_name

def create_chart(df, id, type_chart, year_toggle, range_toggle):
    filtered_df, mapping_name, stocks_in_name = get_data(df, id)
    if type_chart:
        return chart_trend(filtered_df, mapping_name, stocks_in_name)
    else:
        return chart_seasonality(filtered_df, mapping_name, stocks_in_name, year_toggle, range_toggle)

def create_callbacks(app, page_id, num_graphs, idents, data_store_id):
    @app.callback(
        [Output(f'{page_id}-graph-{i}', 'figure') for i in range(1, num_graphs + 1)],
        [Input(f'{page_id}-graph-toggle', 'value'),
        Input(f'{page_id}-year-toggle', 'value'),
        Input(f'{page_id}-toggle-range', 'value'),
        Input(data_store_id, 'data')]
    )
    def update_graphs(toggle_chart, year_toggle, toggle_range, data):
        if data is None:
            print("No data available, cannot update graphs.")  # Add debugging statement to confirm data state
            return [dash.no_update] * num_graphs

        raw_data = pd.DataFrame(data)
        # Ensure 'period' column is handled correctly
        if 'period' in raw_data.columns:
            raw_data['period'] = pd.to_datetime(raw_data['period'])
        else:
            print("Expected 'period' column not found in data.")  # Debugging statement
            return [dash.no_update] * num_graphs

        figures = [
            create_chart(raw_data, ident, toggle_chart, year_toggle, toggle_range) for ident in idents
        ]
        return figures[:num_graphs]
