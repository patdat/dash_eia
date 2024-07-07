import requests
import pandas as pd
import numpy as np
from utils.mapping import production_mapping

def download_raw_file():
    url = "https://ir.eia.gov/wpsr/psw09.xls"
    response = requests.get(url)
    # Save the file to the specified directory
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
    #remove duplicate in period and id
    df = df.drop_duplicates(subset=['period', 'id'])
    return df

def generate_additional_calculation(df):
    df = df.copy()
    crudeRuns = ['WCRRIUS2','WCRRIP12','WCRRIP22','WCRRIP32','WCRRIP42','WCRRIP52',]
    grossRuns = ['WGIRIUS2','WGIRIP12','WGIRIP22','WGIRIP32','WGIRIP42','WGIRIP52',]    
    crudeStocks = ['WCESTUS1','WCESTP11','WCESTP21','WCESTP31','WCESTP41','WCESTP51','W_EPC0_SAX_YCUOK_MBBL']    
    crudeImports = ['WCEIMUS2','WCEIMP12','WCEIMP22','WCEIMP32','WCEIMP42','WCEIMP52',]
    # crudeOriginalAdjustment = ['WCRAUUS2','W_EPC0_TVP_NUS_MBBLD']
    
    # idsToInclude = crudeRuns + grossRuns + crudeStocks + crudeImports + crudeOriginalAdjustment
    idsToInclude = crudeRuns + grossRuns + crudeStocks + crudeImports

    df = df[df['id'].isin(idsToInclude)]

    df = df.pivot(index='period',columns='id',values='value')
    
    #Feedstock Inputs into Refineries
    df['feedstockRunsUS'] = df['WGIRIUS2'] - df['WCRRIUS2']
    df['feddStockRunsP1'] = df['WGIRIP12'] - df['WCRRIP12']
    df['feedstockRunsP2'] = df['WGIRIP22'] - df['WCRRIP22']
    df['feedstockRunsP3'] = df['WGIRIP32'] - df['WCRRIP32']
    df['feedstockRunsP4'] = df['WGIRIP42'] - df['WCRRIP42']
    df['feedstockRunsP5'] = df['WGIRIP52'] - df['WCRRIP52']
    
    #P9 Crude Runs
    df['crudeRunsP9'] = df['WCRRIP22'] + df['WCRRIP32'] + df['WCRRIP42']
    #P9 Gross Runs
    df['grossRunsP9'] = df['WGIRIP22'] + df['WGIRIP32'] + df['WGIRIP42']
    #P9 Feedstock Runs
    df['feedstockRunsP9'] = df['grossRunsP9'] - df['crudeRunsP9']
    #P9 Crude Stocks
    df['crudeStocksP9'] = df['WCESTP21'] + df['WCESTP31'] + df['WCESTP41']
    #P9 Crude Imports
    df['crudeImportsP9'] = df['WCEIMP22'] + df['WCEIMP32'] + df['WCEIMP42']
    #P9 Crude Original Adjustment
    # df['crudeOriginalAdjustment'] = df['WCRAUUS2'] + df['W_EPC0_TVP_NUS_MBBLD']
    #P2E crudeStocksP2E
    df['crudeStocksP2E'] = df['WCESTP21'] - df['W_EPC0_SAX_YCUOK_MBBL']    

    wps_dicts = {
        'feedstockRunsUS' : 'Weekly U.S. Feedstock Inputs into Refineries  (Thousand Barrels per Day)',
        'feddStockRunsP1' : 'Weekly East Coast (PADD 1) Feedstock Inputs into Refineries  (Thousand Barrels per Day)',
        'feedstockRunsP2' : 'Weekly Midwest (PADD 2) Feedstock Inputs into Refineries  (Thousand Barrels per Day)',
        'feedstockRunsP3' : 'Weekly Gulf Coast (PADD 3) Feedstock Inputs into Refineries  (Thousand Barrels per Day)',
        'feedstockRunsP4' : 'Weekly Rocky Mountain (PADD 4) Feedstock Inputs into Refineries  (Thousand Barrels per Day)',
        'feedstockRunsP5' : 'Weekly West Coast (PADD 5) Feedstock Inputs into Refineries  (Thousand Barrels per Day)',
        'crudeRunsP9' : 'Weekly PADD 9 Crude Runs  (Thousand Barrels per Day)',
        'grossRunsP9' : 'Weekly PADD 9 Gross Runs  (Thousand Barrels per Day)',
        'feedstockRunsP9' : 'Weekly PADD 9 Feedstock Runs  (Thousand Barrels per Day)',
        'crudeStocksP9' : 'Weekly PADD 9 Crude Stocks  (Thousand Barrels)',
        'crudeImportsP9' : 'Weekly PADD 9 Crude Imports  (Thousand Barrels per Day)',
        # 'crudeOriginalAdjustment' : 'Weekly US Crude Original Adjustment  (Thousand Barrels per Day)',
        'crudeStocksP2E' : 'Weekly PADD 2 East Coast Crude Stocks  (Thousand Barrels)',
        }
    wps_df = pd.DataFrame(wps_dicts.items(), columns=['id','name'])

    df = df[wps_dicts.keys()]
    df = df.reset_index()
    df = pd.melt(df, id_vars=['period'], value_vars=wps_dicts.keys())
    df = pd.merge(df, wps_df, on='id', how='left')
    return df

def generate_additional_tickers(df):
    df = df.copy()
    dff = generate_additional_calculation(df)
    df = pd.concat([df, dff])
    return df

def generate_adjustment_factor(raw):
    df = raw.copy()
    ids = ['WCRSTUS1','WCRFPUS2','WCEIMUS2','WCRRIUS2','WCREXUS2']
    df = df[df['id'].isin(ids)]
    pv = df.pivot(index='period',columns='id',values='value')
    pv['stock_change'] = pv['WCRSTUS1'].diff() / 7
    pv['adjustment_factor'] = (pv['WCRFPUS2'] + pv['WCEIMUS2'] - pv['WCRRIUS2'] - pv['WCREXUS2'] - pv['stock_change']) * -1
    pv = pv.dropna(subset=['adjustment_factor'])
    pv['adjustment_factor'] = pd.to_numeric(pv['adjustment_factor'], errors='coerce').round(0)
    pv['adjustment_factor'] = pv['adjustment_factor'].astype(int)
    pv['adjustment_factor'] = pv['adjustment_factor'].astype(object)
    pv = pv[['adjustment_factor']].reset_index()
    pv = pv.rename_axis(None, axis=1)
    pv = pv.rename(columns={'adjustment_factor':'value'})
    pv['name'] = 'Weekly U.S. Crude Oil Adjustment Factor  (Thousand Barrels per Day)'
    pv['id'] = 'crudeOriginalAdjustment'
    raw = pd.concat([raw, pv])
    return raw

def add_uom(df):
    df = df.copy()
    df['uom'] = 'kbd'
    df.loc[df['name'].str.contains('stock', case=False), 'uom'] = 'kb'
    df.loc[df['name'].str.contains('percent', case=False), 'uom'] = 'pct'    
    df.loc[df['name'].str.contains('feedstock', case=False), 'uom'] = 'kbd'
    return df

def filter_data(df):
    df = df.copy()
    mapping = list(production_mapping.keys())
    df = df[df['id'].isin(mapping)]
    return df

def reorder_columns(df):
    df = df.copy()
    #id,name,uom,period,value
    df = df[['id','name','uom','period','value']]
    return df

def pivot_data(df):
    df = df.copy()
    df = df.pivot(index='period',columns='id',values='value').reset_index()
    return df

def main():
    download_raw_file()
    sheets = read_excel_file()
    df = parse_all_data(sheets)
    df = generate_additional_tickers(df)
    df = generate_adjustment_factor(df)
    df = df[df['period'] >= '2014-12-26']
    df = add_uom(df)
    df = filter_data(df)
    df = reorder_columns(df)
    df.to_csv('./data/wps_gte_2015.csv',index=False)
    pv = pivot_data(df)
    pv.to_csv('./data/wps_gte_2015_pivot.csv',index=False)    
    return pv

if __name__ == '__main__':
    df = main()


