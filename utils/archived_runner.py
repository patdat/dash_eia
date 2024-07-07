import pandas as pd
import numpy as np
import dash
from dash import html, dash_table

def first_pass(df):    
    df = df.copy()
    df.iloc[:, 2:] = df.iloc[:, 2:].replace(',', '', regex=True)
    df.iloc[:, 2:] = df.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')
    df = df.iloc[:, :-3]
    df = df.dropna(subset=[df.columns[2]])
    df.iloc[:, 2:] = df.iloc[:, 2:].round(2)

    df.loc[:, 'wow'] = df.iloc[:, 2] - df.iloc[:, 3]
    df.loc[:, 'yoy'] = df.iloc[:, 2] - df.iloc[:, 4]

    df = df.drop(df.columns[4], axis=1)
    df['STUB_1'] = df['STUB_1'].str.lower()
    df['STUB_2'] = df['STUB_2'].str.lower()
    df['STUB_2'] = df['STUB_2'].str.replace("'", "")
    df['STUB_2'] = df['STUB_2'].str.replace('&', 'and')
    return df

def second_pass(df):
    locations_dict = {
        'p1': 'east coast (padd 1)',
        'p2': 'midwest (padd 2)',
        'p3': 'gulf coast (padd 3)',
        'p4': 'rocky mountain (padd 4)',
        'p5': 'west coast (padd 5)',
        'p45': "padds 4 and 5",
        'p1a': 'new england (padd 1a)',
        'p1b': 'central atlantic (padd 1b)',
        'p1c': 'lower atlantic (padd 1c)',
        'us': 'us'    
    }

    df['location'] = np.where(df['STUB_2'].isin(list(locations_dict.values())), df['STUB_2'], 'us')
    df['category'] = np.where(df['location'] == 'us', df['STUB_2'], None)
    df['category'] = df['category'].fillna(method='ffill')

    df = df.rename(columns={'STUB_1': 'aspect'})
    pop = df.pop('location')
    df.insert(2, 'location', pop)

    pop = df.pop('category')
    df.insert(3, 'category', pop)

    df = df.drop_duplicates(subset=['aspect', 'location', 'category'])

    locations_dict_inverted = {value: key for key, value in locations_dict.items()}
    df['location'] = df['location'].map(locations_dict_inverted)

    df = df.drop(df.columns[1], axis=1)    
    
    return df

def download_data():
    try:
        df = pd.read_csv('https://ir.eia.gov/wpsr/table9.csv', encoding='ISO-8859-1')
        isAvailable = True
    except:
        df = pd.DataFrame()
        df['aspect'] = ['A', 'B', 'C', 'D', 'E']
        df['location'] = ['p1', 'p2', 'p3', 'p4', 'p5']
        df['category'] = ['a', 'b', 'c', 'd', 'e']
        df['now'] = [1, 2, 3, 4, 5]
        df['prior'] = [1, 2, 3, 4, 5]
        df['wow'] = [0, 0, 0, 0, 0]
        df['yoy'] = [0, 0, 0, 0, 0]        
        isAvailable = False
        
    if isAvailable:
        df = first_pass(df)
        df = second_pass(df)        
        
    return df, isAvailable
    
df, isAvailable = download_data()    

# Initialize the app
app = dash.Dash(__name__)

# Fetch and process the data
df, isAvailable = download_data()

# Define the app layout
layout = html.Div([
    html.H1("Data Overview"),
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'}
    )
])



# lst_aspect = [
# 'crude oil production ',
# 'crude oil production ',
# 'crude oil production ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'refiner inputs and utilization ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'stocks (million barrels) ',
# 'product supplied ',
# 'product supplied ',
# 'product supplied ',
# 'product supplied ',
# 'product supplied ',
# 'product supplied ',
# 'product supplied ',    
# ]

# lst_location = [
# 'us',
# 'us',
# 'us',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'us',
# 'p1',
# 'p2',
# 'us',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'us',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'p4',
# 'p5',
# 'us',
# 'p1',
# 'p2',
# 'p3',
# 'us',
# 'us',
# 'us',
# 'us',
# 'us',
# 'us',
# 'us',
# 'us',    
# ]

# lst_category = [
# 'domestic production',
# 'alaska',
# 'lower 48',
# 'crude oil inputs',
# 'crude oil inputs',
# 'crude oil inputs',
# 'crude oil inputs',
# 'crude oil inputs',
# 'crude oil inputs',
# 'gross inputs',
# 'gross inputs',
# 'gross inputs',
# 'gross inputs',
# 'gross inputs',
# 'gross inputs',
# 'operable capacity',
# 'operable capacity',
# 'operable capacity',
# 'operable capacity',
# 'operable capacity',
# 'operable capacity',
# 'percent utilization',
# 'percent utilization',
# 'percent utilization',
# 'percent utilization',
# 'percent utilization',
# 'percent utilization',
# 'crude oil (including spr)',
# 'commercial',
# 'commercial',
# 'commercial',
# 'cushing, oklahoma',
# 'cushing, oklahoma',
# 'cushing, oklahoma',
# 'cushing, oklahoma',
# 'alaska in-transit',
# 'spr',
# 'total motor gasoline',
# 'total motor gasoline',
# 'total motor gasoline',
# 'total motor gasoline',
# 'total motor gasoline',
# 'total motor gasoline',
# 'kerosene-type jet fuel',
# 'kerosene-type jet fuel',
# 'kerosene-type jet fuel',
# 'kerosene-type jet fuel',
# 'kerosene-type jet fuel',
# 'kerosene-type jet fuel',
# 'distillate fuel oil',
# 'distillate fuel oil',
# 'distillate fuel oil',
# 'distillate fuel oil',
# 'distillate fuel oil',
# 'distillate fuel oil',
# 'residual fuel oil',
# 'residual fuel oil',
# 'residual fuel oil',
# 'residual fuel oil',
# 'residual fuel oil',
# 'residual fuel oil',
# 'propane/propylene',
# 'propane/propylene',
# 'propane/propylene',
# 'propane/propylene',
# 'padds 4 and 5 ',
# 'total product supplied',
# 'finished motor gasoline',
# 'kerosene-type jet fuel',
# 'distillate fuel oil',
# 'residual fuel oil',
# 'propane/propylene',
# 'other oils',    
# ]    

# df_lst = pd.DataFrame({'aspect': lst_aspect, 'location': lst_location, 'category': lst_category})
# df = pd.merge(df, df_lst, on=['aspect', 'location', 'category'], how='inner')