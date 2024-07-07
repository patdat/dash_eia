import pandas as pd

def generate_additional_calculation(df):
    df = df.copy()
    crudeRuns = ['WCRRIUS2','WCRRIP12','WCRRIP22','WCRRIP32','WCRRIP42','WCRRIP52',]
    grossRuns = ['WGIRIUS2','WGIRIP12','WGIRIP22','WGIRIP32','WGIRIP42','WGIRIP52',]    
    crudeStocks = ['WCESTUS1','WCESTP11','WCESTP21','WCESTP31','WCESTP41','WCESTP51','W_EPC0_SAX_YCUOK_MBBL']    
    crudeImports = ['WCEIMUS2','WCEIMP12','WCEIMP22','WCEIMP32','WCEIMP42','WCEIMP52',]
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
    #P2E crudeStocksP2E
    df['crudeStocksP2E'] = df['WCESTP21'] - df['W_EPC0_SAX_YCUOK_MBBL']    

    wps_dicts = {
        'feedstockRunsUS' : 'US Feedstock Runs (kbd)',
        'feddStockRunsP1' : 'P1 Feedstock Runs (kbd)',
        'feedstockRunsP2' : 'P2 Feedstock Runs (kbd)',
        'feedstockRunsP3' : 'P3 Feedstock Runs (kbd)',
        'feedstockRunsP4' : 'P4 Feedstock Runs (kbd)',
        'feedstockRunsP5' : 'P5 Feedstock Runs (kbd)',
        'crudeRunsP9' : 'P9 Crude Runs (kbd)',
        'grossRunsP9' : 'P9 Gross Runs (kbd)',
        'feedstockRunsP9' : 'P9 Feedstock Runs (kbd)',
        'crudeStocksP9' : 'P9 Stocks (kb)',
        'crudeImportsP9' : 'P9 Crude Imports (kbd)',
        'crudeStocksP2E' : 'P2E Stocks (kb)',
        }
    wps_df = pd.DataFrame(wps_dicts.items(), columns=['id','name'])

    df = df[wps_dicts.keys()]
    df = df.reset_index()
    df = pd.melt(df, id_vars=['period'], value_vars=wps_dicts.keys())
    df = pd.merge(df, wps_df, on='id', how='left')
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
    pv['name'] = 'OG Adjustment Factor (kbd)'
    pv['id'] = 'crudeOriginalAdjustment'
    raw = pd.concat([raw, pv])
    return raw

def generate_additional_tickers(df):
    df = df.copy()
    dff = generate_additional_calculation(df)
    df = pd.concat([df, dff])
    df = generate_adjustment_factor(df)
    df = df.drop(columns=['name'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df