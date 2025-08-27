import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def create_date_range(start, end):
    """Create a DataFrame with year and month columns for data pulling."""
    years = range(start, end + 1)
    months = range(1, 13)
    data = [{'year': year, 'month': f'{month:02d}'} for year in years for month in months]
    return pd.DataFrame(data)

def get_most_recent_release():
    """Get the release date for the most recent data (3 months ago)."""
    today = datetime.today()
    three_months_ago = today - relativedelta(months=2)
    return three_months_ago.year, three_months_ago.month

def clean_data(df):
    """Clean the raw DataFrame."""
    df = df.copy()
    df['RPT_PERIOD'] = pd.to_datetime(df['RPT_PERIOD']) + pd.offsets.MonthBegin(-1)
    # Ensure GCTRY_CODE is consistently typed as string
    if 'GCTRY_CODE' in df.columns:
        df['GCTRY_CODE'] = df['GCTRY_CODE'].astype(str)
    return df

def main(start=2017, end=2030):
    """Fetch archived data from the EIA website."""
    date_range = create_date_range(start, end)
    max_year, max_month = get_most_recent_release()
    archived_data = pd.DataFrame()

    for _, row in date_range.iterrows():
        year, month = row['year'], row['month']
        url = f"https://www.eia.gov/petroleum/imports/companylevel/archive/{year}/{year}_{month}/data/import.xlsx"
        print(f"Fetching: {year}-{month}")
        
        try:
            df = pd.read_excel(url, sheet_name='IMPORTS')
            archived_data = pd.concat([archived_data, df])
        except:
            print(f"Error: {year}-{month}")
            break

    return clean_data(archived_data)

# Main code execution
if __name__ == "__main__":
    df = main()
    df.to_parquet("./data/cli/companylevelimports.parquet", index=False,compression='zstd',engine='pyarrow')
