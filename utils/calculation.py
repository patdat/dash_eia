import pandas as pd
from utils.graph_seag import chart_seasonality
from utils.graph_line import chart_trend
from utils.mapping import production_mapping
from dash import Output, Input

# Load initial data only once
def get_initial_data():
    df = pd.read_csv('./data/wps_gte_2015.csv', parse_dates=['period'])
    df = df[df['period'] > '2015-01-01']
    df = df.drop(columns=['uom'])
    return df

def get_data(df, id):
    # Filter and transform data specific to the identifier
    filtered_df = df[df['id'] == id].copy()
    name = filtered_df['name'].iloc[0]
    filtered_df = filtered_df[['period', 'value']]
    
    mapping_name = production_mapping.get(id, name)
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

def create_callbacks(app, page_id, num_graphs, idents, raw_data):
    @app.callback(
        [Output(f'{page_id}-graph-{i}', 'figure') for i in range(1, num_graphs + 1)],
        [Input(f'{page_id}-graph-toggle', 'value'),
         Input(f'{page_id}-year-toggle', 'value'),
         Input(f'{page_id}-toggle-range', 'value')]
    )
    def update_graphs(toggle_chart, year_toggle, toggle_range):
        figures = [create_chart(raw_data, ident, toggle_chart, year_toggle, toggle_range) for ident in idents]
        return figures[:num_graphs]
