import requests
import pandas as pd
import numpy as np
from utils.mapping import production_mapping
from utils.generate_additional_tickers import generate_additional_tickers

def download_raw_file():
    url = "https://ir.eia.gov/wpsr/psw09.xls"
    response = requests.get(url)
    file_path = "./data/eia_weekly_psw09.xls"
    with open(file_path, "wb") as file:
        file.write(response.content)

def read_excel_file():
    file_path = './data/eia_weekly_psw09.xls'
    sheets = pd.read_excel(file_path, sheet_name=None)
    contents = sheets.pop('Contents')
    return sheets

def parse_data(df):
    df = df.copy()
    df.columns = df.iloc[0] + '___' + df.iloc[1]
    df = df.drop([0, 1])
    df = df.rename(columns={df.columns[0]: 'period'})
    df['period'] = pd.to_datetime(df['period'])
    df = df[df['period'] >= '2014-12-19']
    df = df.melt(id_vars=['period'], var_name='id', value_name='value')
    df[['id', 'name']] = df['id'].str.split('___', expand=True)
    return df

def parse_all_data(sheets):
    df = pd.DataFrame()
    for sheet in sheets:
        df = pd.concat([df, parse_data(sheets[sheet])])
    df = df.drop_duplicates(subset=['period', 'id'])
    df = df.drop('name', axis=1)  
    return df

def filter_data(df):
    df = df.copy()
    mapping = list(production_mapping.keys())
    df = df[df['id'].isin(mapping)]
    return df

def map_name(df):
    df = df.copy()
    df['name'] = df['id'].map(production_mapping)
    return df

def reorder_columns(df):
    df = df.copy()
    cols = ['period', 'id', 'name', 'value']
    df = df[cols]
    return df

def pivot_data(df):
    df = df.copy()
    df = df.pivot(index='period',columns='id',values='value').reset_index()
    return df

def main():
    try:
        download_raw_file()
        sheets = read_excel_file()
        df = parse_all_data(sheets)
        df = generate_additional_tickers(df)
        df = df[df['period'] >= '2014-12-26']
        df = filter_data(df)
        df = map_name(df)
        df = reorder_columns(df)
        df.to_csv('./data/wps_gte_2015.csv',index=False)
        pv = pivot_data(df)
        pv.to_csv('./data/wps_gte_2015_pivot.csv',index=False)    
    except Exception as e:
        print('using local file instead b/c data not available:', e)
        pv = pd.read_csv('./data/wps_gte_2015_pivot.csv',parse_dates=['period'])
    return pv

if __name__ == '__main__':
    main()