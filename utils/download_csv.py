import pandas as pd
import numpy as np
from utils.mapping import production_mapping
from utils.generate_additional_tickers import generate_additional_tickers

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
    df['category'] = df['category'].ffill()

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

def third_pass(df):
    df = df.copy()
    mapping = pd.read_csv('./lookup/09_csv_mapping.csv')
    df['lookup'] = df['aspect'] + df['location'] + df['category']
    df = mapping.merge(df, left_on='lookup', right_on='lookup', how='left')
    return df

def fourth_pass(df):
    df = df.copy()
    df = df.drop(['lookup', 'aspect', 'location', 'category', 'wow','yoy'], axis=1)
    df = df.drop_duplicates(subset='id')
    df = df.melt(id_vars=['id'], var_name='period', value_name='value')
    df['period'] = pd.to_datetime(df['period'], format='%m/%d/%y')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.sort_values(['period', 'id'])
    return df
    
def fifth_pass(df):
    df = df.copy()
    df['name'] = df['id'].map(production_mapping)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.loc[df['name'].str.contains('stocks', case=False), 'value'] *= 1000
    #if name doesn't contain (pct) then round to 0
    df.loc[~df['name'].str.contains('pct', case=False), 'value'] = df['value'].round(0)
    df = df[['id', 'period', 'value']]
    return df

def sixth_pass(df):
    df = df.copy()
    df = generate_additional_tickers(df)
    df = df[df['period'] == df['period'].max()]
    return df

def seventh_pass(df):
    df = df.copy()
    df['name'] = df['id'].map(production_mapping)
    df = df[['period', 'id', 'name', 'value']]
    return df

def download_data():
    try:
        df = pd.read_csv('https://ir.eia.gov/wpsr/table9.csv', encoding='ISO-8859-1')
        print('Data downloaded from EIA')
        isAvailable = True
    except Exception as e:    
        isAvailable = False
        print('using local file instead b/c data not available:', e,)
        return pd.read_csv('./data/eia_weekly_fast_download_psw09.csv'), isAvailable
    
    if isAvailable:
        df = first_pass(df)
        df = second_pass(df)    
        df = third_pass(df)    
        df = fourth_pass(df)
        df = fifth_pass(df)
        df = sixth_pass(df)
        df = seventh_pass(df)
        df.to_csv('./data/eia_weekly_fast_download_psw09.csv', index=False)    
        
    return df, isAvailable

def pivot_data(df):
    df = df.copy()
    df = df.pivot(index='period',columns='id',values='value').reset_index()
    return df

def main():
    df, isAvailable = download_data()
    print(isAvailable)
    
    if isAvailable:
        df = df.copy()
        max_date = df['period'].max()
        master = pd.read_csv('./data/wps_gte_2015.csv',parse_dates=['period'])
        master = master[master['period'] != max_date]
        df = pd.concat([master, df], ignore_index=True)
        df = df.sort_values(['id', 'period'])
        df.to_csv('./data/wps_gte_2015.csv', index=False)
        pv = pivot_data(df)
        pv.to_csv('./data/wps_gte_2015_pivot.csv',index=False)    
    else:
        pv = pd.read_csv('./data/wps_gte_2015_pivot.csv',parse_dates=['period'])
    return pv