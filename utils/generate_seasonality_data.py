from utils.mapping import production_mapping
from utils.calculation import get_initial_data 
import pandas as pd

def add_weekOfYear_Year(df):
    df = df.copy()
    df.insert(0,'week_of_year',df['period'].dt.isocalendar().week)
    df.insert(1,'year',df['period'].dt.year)
    df = df[df['week_of_year'] <= 52]
    return df

def select_seasonality_range(df, range_selector):
    df = df.copy()
    
    if range_selector == '1519':
        years = [2015, 2016, 2017, 2018, 2019]
    elif range_selector == '1823':
        years = [2018, 2019, 2021, 2022, 2023]
    
    def get_min_max(df, min_or_max, years):
        df = df.copy()
        df = df[df['year'].isin(years)]
        df = df.drop(columns=['period', 'year'])
        if min_or_max == 'min':
            df = df.groupby(['week_of_year']).min().reset_index()
        elif min_or_max == 'max':
            df = df.groupby(['week_of_year']).max().reset_index()
        return df

    def get_average(df, years):
        df = df[df['year'].isin(years)]
        df = df.drop(columns=['period', 'year'])
        df = df.groupby(['week_of_year']).mean().reset_index()
        df.insert(0, 'type', f'average_{range_selector}')    
        return df

    df_min = get_min_max(df, 'min', years)
    df_min.insert(0, 'type', f'min_{range_selector}')
    
    df_max = get_min_max(df, 'max', years)
    df_max.insert(0, 'type', f'max_{range_selector}')
        
    df_average = get_average(df, years)
    
    dff = pd.concat([df_min, df_max,df_average])
    
    return dff


def get_seasonality_data(df):
    df = df.copy()
    # df = extend_df(df)
    df = add_weekOfYear_Year(df)

    df_1519 = select_seasonality_range(df, '1519')
    df_1823 = select_seasonality_range(df, '1823')    

    df.insert(0, 'type', 'actual')
    df['type'] = df['type'] + '_' + df['year'].astype(str)
    df.drop(columns=['year'], inplace=True)

    df = pd.concat([df,df_1519, df_1823])    
    df['week_of_year'] = df['week_of_year'].astype(int)
    
    df['period'] = pd.to_datetime(df['period'])
    
    
    def format_date(date):
        return date.strftime('%b %d') if pd.notnull(date) else 'No Date'    
    df['period'] = df['period'].apply(format_date)
    
    def format_value_case_insensitive(val, column_name):
        if "stocks" in column_name.lower():
            val = val/1000
        return val
        

    df = df.set_index(['type','week_of_year','period'])
    cols = df.columns
    cols = [production_mapping[col] for col in cols]
    df.columns = cols

    for column in df.columns:
        df[column] = df[column].apply(lambda x: format_value_case_insensitive(x, column))

    reversed_mapping = {v: k for k, v in production_mapping.items()}
    df.columns = [reversed_mapping[col] for col in df.columns]
    
    df = df.reset_index()
    

    return df

def pivot_individual_data(df,id):
    
    def get_individual_data(df, id):
        cols = ['type','week_of_year','period', id] 
        df = df[cols]
        df = df.rename(columns={id: 'value'})
        type_to_remove = ['actual_2015', 'actual_2016', 'actual_2017', 'actual_2018', 'actual_2019','actual_2020','actual_2021']
        df = df[~df['type'].isin(type_to_remove)]        
        return df    
    
    df = df.copy()
    df = get_individual_data(df, id)

    pivot_values = df.pivot_table(index=['week_of_year'], columns='type', values='value', aggfunc='first')
    pivot_dates = df[df['type'].str.contains('actual')].pivot_table(index=['week_of_year'], columns='type', values='period', aggfunc='first')
    pivot_dates.columns = [f'dates_{col}' for col in pivot_dates.columns]
    df = pd.concat([pivot_dates, pivot_values], axis=1)
    df.reset_index(inplace=True)
    df.columns.name = None
    df.insert(0, 'id', id)
    return df

def generate_seasonality_data():
    ids = list(production_mapping.keys())
    df = get_seasonality_data(get_initial_data())
    dfs = pd.DataFrame()
    for id in ids:
        dfs = pd.concat([dfs, pivot_individual_data(df, id)])
        # df = pivot_individual_data(raw, id)
        # dfs = {**dfs, **{id: pivot_individual_data(df, id)}}
    dfs.reset_index(drop=True, inplace=True)    
    dfs.to_feather('data/seasonality_data.feather')    
    
if __name__ == '__main__':
    generate_seasonality_data()