import pandas as pd

def read_pivot_master():
    df = pd.read_feather('./data/steo/steo_pivot.feather')
    return df

def melt_pivot(df):
    df = pd.melt(df, id_vars=['id','name','release_date'], var_name='period', value_name='value')
    df = df.dropna(subset=['value'])
    df['release_date'] = pd.to_datetime(df['release_date'])
    df['period'] = pd.to_datetime(df['period'])
    
    return df

