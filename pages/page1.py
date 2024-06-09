import dash
import dash_daq as daq
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from app import app  # Import the central app instance assuming 'app.py' initializes it

# Load and preprocess data
raw = pd.read_csv('./data/wps.csv', parse_dates=['period'])
raw = raw[raw['period'] >= '2014-12-26']
raw['name'] = raw['name'].str.lower()

production_mapping = raw[['id','name']].drop_duplicates().copy()
production_mapping = raw.set_index('id').to_dict()['name']

idents = [
    #Crude Production
    'WCRFPUS2', 'W_EPC0_FPF_R48_MBBLD', 'W_EPC0_FPF_SAK_MBBLD',
    #Crude Imports
    'WCEIMUS2','WCEIMP12','WCEIMP22','WCEIMP32','WCEIMP42','WCEIMP52',
    #Crude Refinery Runs
    'WCRRIUS2','WCRRIP12','WCRRIP22','WCRRIP32','WCRRIP42','WCRRIP52',
    #Crude Exports
    'WCREXUS2',
    #Crude PADD Stocks
    'WCESTUS1','WCESTP11','WCESTP21','WCESTP31','WCESTP41','WCESTP51',
    #Crude Other Stock
    'W_EPC0_SAX_YCUOK_MBBL','W_EPC0_SKA_NUS_MBBL','WCSSTUS1','WCRSTUS1',
    #Refinery Utilization
    'WPULEUS3','W_NA_YUP_R10_PER','W_NA_YUP_R20_PER','W_NA_YUP_R30_PER','W_NA_YUP_R40_PER','W_NA_YUP_R50_PER',
    #Refinery Feedstock Runs
    'feedstockRunsUS','feddStockRunsP1','feedstockRunsP2','feedstockRunsP3','feedstockRunsP4','feedstockRunsP5',    
    #Refinery Gross Runs
    'WGIRIUS2','WGIRIP12','WGIRIP22','WGIRIP32','WGIRIP42','WGIRIP52',
    #Crude Imports by Country
    'W_EPC0_IM0_NUS-NBR_MBBLD','W_EPC0_IM0_NUS-NCA_MBBLD','W_EPC0_IM0_NUS-NCO_MBBLD','W_EPC0_IM0_NUS-NEC_MBBLD','W_EPC0_IM0_NUS-NIZ_MBBLD','W_EPC0_IM0_NUS-NMX_MBBLD','W_EPC0_IM0_NUS-NNI_MBBLD','W_EPC0_IM0_NUS-NRS_MBBLD','W_EPC0_IM0_NUS-NSA_MBBLD'
    ]


class DataProcessor:
    def __init__(self, df):
        self.raw = df.copy()

    def interpolate_segment(self, identification):
        df = self.raw[self.raw['id'] == identification]
        df.reset_index(drop=True, inplace=True)
        df.set_index("period", inplace=True)
        df = df.resample('D').interpolate(method='time').bfill().reset_index()
        df = df[df['period'] >= '2015-01-01']
        df = df[['period', 'value']]
        return df

    def get_seasonality_data(self, identification):
        df = self.interpolate_segment(identification)
        data = df.copy()
        data['Date'] = pd.to_datetime(data['period'])
        data['Year'] = data['Date'].dt.year
        data['DayOfYear'] = data['Date'].dt.dayofyear

        min_max_2015_2019 = data[data['Year'].isin([2015, 2016, 2017, 2018, 2019])].groupby('DayOfYear')['value'].agg(['min', 'max']).rename(columns={'min': 'min_1519', 'max': 'max_1519'})
        min_max = data[data['Year'].isin([2018, 2019, 2021, 2022, 2023])].groupby('DayOfYear')['value'].agg(['min', 'max']).rename(columns={'min': 'min_range', 'max': 'max_range'})
        average_2015_2019 = data[data['Year'].isin([2015, 2016, 2017, 2018, 2019])].groupby('DayOfYear')['value'].mean().rename('avg_2015_2019')
        average_range = data[data['Year'].isin([2018, 2019, 2021, 2022, 2023])].groupby('DayOfYear')['value'].mean().rename('avg_range')

        year_data = {year: data[data['Year'] == year].set_index('DayOfYear')['value'].rename(f'Value_{year}') for year in [2021, 2022, 2023, 2024]}

        final_df = pd.concat([min_max_2015_2019, min_max, average_2015_2019, average_range, *year_data.values()], axis=1)
        return final_df

def get_month_starts(year):
    starts = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', freq='MS').dayofyear
    return starts.tolist()
month_starts = get_month_starts(2020)

app = dash.Dash(__name__)

@app.callback(
    [
        #Crude Production
        Output('graph-1', 'figure'),
        Output('graph-2', 'figure'),
        Output('graph-3', 'figure'),
        #Crude Refinery Runs
        Output('graph-4', 'figure'),
        Output('graph-5', 'figure'),
        Output('graph-6', 'figure'),
        Output('graph-7', 'figure'),
        Output('graph-8', 'figure'),
        Output('graph-9', 'figure'),
        #Crude Imports
        Output('graph-10', 'figure'),
        Output('graph-11', 'figure'),
        Output('graph-12', 'figure'),
        Output('graph-13', 'figure'),
        Output('graph-14', 'figure'),
        Output('graph-15', 'figure'), 
        #Crude PADD Stocks
        Output('graph-16', 'figure'),
        Output('graph-17', 'figure'),
        Output('graph-18', 'figure'),
        Output('graph-19', 'figure'),
        Output('graph-20', 'figure'),
        Output('graph-21', 'figure'),
        #Crude Other Stock
        Output('graph-22', 'figure'),
        Output('graph-23', 'figure'),
        Output('graph-24', 'figure'),
        Output('graph-25', 'figure'),      
        #Crude Exports
        Output('graph-26', 'figure'),
        #Refinery Utilization
        Output('graph-27', 'figure'),
        Output('graph-28', 'figure'),
        Output('graph-29', 'figure'),
        Output('graph-30', 'figure'),
        Output('graph-31', 'figure'),
        Output('graph-32', 'figure'),
        #Refinery Feedstock Runs
        Output('graph-33', 'figure'),
        Output('graph-34', 'figure'),
        Output('graph-35', 'figure'),
        Output('graph-36', 'figure'),
        Output('graph-37', 'figure'),
        Output('graph-38', 'figure'),
        #Refinery Gross Runs
        Output('graph-39', 'figure'),
        Output('graph-40', 'figure'),
        Output('graph-41', 'figure'),
        Output('graph-42', 'figure'),
        Output('graph-43', 'figure'),
        Output('graph-44', 'figure'),
        #Crude Imports by Country
        Output('graph-45', 'figure'),
        Output('graph-46', 'figure'),
        Output('graph-47', 'figure'),
        Output('graph-48', 'figure'),
        Output('graph-49', 'figure'),
        Output('graph-50', 'figure'),
        Output('graph-51', 'figure'),
        Output('graph-52', 'figure'),
        Output('graph-53', 'figure'),
     ],
    [Input('year-toggle', 'value'),
     Input('toggle-range', 'value')]
)
def update_graphs(selected_years, toggle_state):
    processor = DataProcessor(raw)
    figures = []
    
    
    
    
    for ident in idents:
        df = processor.get_seasonality_data(ident)
        figures.append(create_chart(df, selected_years, toggle_state, ident))
    return figures

def create_chart(df, selected_years, toggle_active, ident):
    min_key = 'min_1519' if toggle_active else 'min_range'
    max_key = 'max_1519' if toggle_active else 'max_range'
    production_name = production_mapping.get(ident, 'Unknown Production')

    data = [
        go.Scatter(x=df.index, y=df[min_key], fill=None, mode='lines', line_color='#cccccc', name=f'{production_name} Historical Min'),
        go.Scatter(x=df.index, y=df[max_key], fill='tonexty', mode='lines', line_color='#cccccc', name=f'{production_name} Historical Max'),
        go.Scatter(x=df.index, y=df['avg_range'], mode='lines', line=dict(color='black', dash='dash'), name=f'{production_name} Current Average')
    ]
    
    for year in selected_years:
        if f'Value_{year}' in df.columns:
            data.append(go.Scatter(x=df.index, y=df[f'Value_{year}'], mode='lines', name=f'{production_name} Value {year}', line=dict(color={'2022': 'green', '2023': 'blue', '2024': 'red'}[year])))

    return {
        'data': data,
        'layout': go.Layout(
            title=f'{production_name}',
            xaxis=dict(showgrid=False, tickangle=90, tickvals=month_starts, ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']),
            yaxis=dict(showgrid=False),
            hovermode='closest',
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=30),
            # height=600,
            # width=500
        )
    }

layout = html.Div([
    
    html.Div([
        html.Div([            
            dcc.Checklist(
                id='year-toggle',
                options=[
                    {"label": html.Div(['22'], style={'color': 'white', 'font-size': '20px', 'background-color': 'green', 'padding': '10px', 'border-radius': '5px'}), "value": '2022'},
                    {"label": html.Div(['23'], style={'color': 'white', 'font-size': '20px', 'background-color': 'blue', 'padding': '10px', 'border-radius': '5px'}), "value": '2023'},
                    {"label": html.Div(['24'], style={'color': 'white', 'font-size': '20px', 'background-color': 'red', 'padding': '10px', 'border-radius': '5px'}), "value": '2024'},
                ],
                value=['2022', '2023', '2024'],  # Default is all selected
                inline=True,
                labelStyle={"display": "flex", "align-items": "center", "margin-right": "20px", "font-size": "20px"},  # Ensure spacing and alignment
                style={'padding': '10px', 'font-size': '16px', 'display': 'flex', 'justify-content': 'right'}  # Center the checklist
            ),
        ], style={'padding': '10px', 'flex': '1'}),
        html.Div([
            daq.ToggleSwitch(
                id='toggle-range',
                label='Toggle 2018-2023 (ex 2020) or 2015-2019',
                labelPosition='right',
                value=False,
                style={'margin-top': '20px', 'margin-bottom': '20px'}
            ),
        ], style={'padding': '10px', 'flex': '1', 'display': 'flex', 'justify-content': 'flex-start'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', 'position': 'fixed', 'top': '0', 'left': '0', 'right': '0', 'background-color': '#fff', 'z-index': '1000', 'box-shadow': '0px 2px 5px rgba(0,0,0,0.2)'}),

    #blank space
    html.Div([html.H1('__', style={'text-align': 'left', 'margin-top': '50px'})]),    


    html.Div([html.H1('Crude Oil Production', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-1'),
        dcc.Graph(id='graph-2'),
        dcc.Graph(id='graph-3'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),

    # ], style={'display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '2px'}),

    html.Div([html.H1('Crude Imports', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-4'),
        dcc.Graph(id='graph-5'),
        dcc.Graph(id='graph-6'),
        dcc.Graph(id='graph-7'),
        dcc.Graph(id='graph-8'),
        dcc.Graph(id='graph-9'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),

    html.Div([html.H1('Crude Refinery Runs', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-10'),
        dcc.Graph(id='graph-11'),
        dcc.Graph(id='graph-12'),
        dcc.Graph(id='graph-13'),
        dcc.Graph(id='graph-14'),
        dcc.Graph(id='graph-15'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),

    html.Div([html.H1('Crude Exports', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-26'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),


    html.Div([html.H1('Crude PADD Stocks', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-16'),
        dcc.Graph(id='graph-17'),
        dcc.Graph(id='graph-18'),
        dcc.Graph(id='graph-19'),
        dcc.Graph(id='graph-20'),
        dcc.Graph(id='graph-21'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),

    html.Div([html.H1('Crude PADD Stocks', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-22'),
        dcc.Graph(id='graph-23'),
        dcc.Graph(id='graph-24'),
        dcc.Graph(id='graph-25'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),

    html.Div([html.H1('Refinery Utilization', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-27'),
        dcc.Graph(id='graph-28'),
        dcc.Graph(id='graph-29'),
        dcc.Graph(id='graph-30'),
        dcc.Graph(id='graph-31'),
        dcc.Graph(id='graph-32'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),
    
    html.Div([html.H1('Refinery Feedstock Runs', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-33'),
        dcc.Graph(id='graph-34'),
        dcc.Graph(id='graph-35'),
        dcc.Graph(id='graph-36'),
        dcc.Graph(id='graph-37'),
        dcc.Graph(id='graph-38'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),
    
    html.Div([html.H1('Refinery Gross Runs', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-39'),
        dcc.Graph(id='graph-40'),
        dcc.Graph(id='graph-41'),
        dcc.Graph(id='graph-42'),
        dcc.Graph(id='graph-43'),
        dcc.Graph(id='graph-44'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),
    
    html.Div([html.H1('Crude Imports by Country', style={'text-align': 'left', 'margin-top': '50px'})]),
    html.Div([
        dcc.Graph(id='graph-45'),
        dcc.Graph(id='graph-46'),
        dcc.Graph(id='graph-47'),
        dcc.Graph(id='graph-48'),
        dcc.Graph(id='graph-49'),
        dcc.Graph(id='graph-50'),
        dcc.Graph(id='graph-51'),
        dcc.Graph(id='graph-52'),
        dcc.Graph(id='graph-53'),
    ], style={'display': 'flex', 'justify-content': 'space-around','display': 'grid', 'grid-template-columns': 'repeat(3, 1fr)', 'grid-gap': '20px'}),


], style={'margin-top': '50px'})

if __name__ == '__main__':
    app.run_server(debug=True)
