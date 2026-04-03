import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)

# Input/Output configuration
INPUT_PARQUET = './data/eia/ingestion/wps.parquet'

OUTPUT_DIRECTORY_FOR_ADDITIONAL_FILES = './data/eia/processed'
WPS_MONTHLY_FILE = os.path.join(OUTPUT_DIRECTORY_FOR_ADDITIONAL_FILES, 'wps_monthly.parquet')
WPS_MONTHLY_PIVOT_FILE = os.path.join(OUTPUT_DIRECTORY_FOR_ADDITIONAL_FILES, 'wps_monthly_pivot.csv')
WPS_WEEKLY_PIVOT_FILE = os.path.join(OUTPUT_DIRECTORY_FOR_ADDITIONAL_FILES, 'wps_weekly_pivot.csv')


def load_wps_data():
    """Load WPS data from parquet."""
    if os.path.exists(INPUT_PARQUET):
        logger.info(f"Reading from parquet: {INPUT_PARQUET}")
        df = pd.read_parquet(INPUT_PARQUET)
    else:
        raise FileNotFoundError(f"{INPUT_PARQUET} not found. Please run ingester first.")

    df['date'] = pd.to_datetime(df['date'])
    # Uppercase series_id for consistent matching
    df['series_id'] = df['series_id'].astype(str).str.strip().str.upper()
    return df


def process_storage_items(df):
    """Process storage/stock items - interpolate to month-end when needed.

    Uses series name to detect stock items (contains 'STOCK').
    """
    if df.empty:
        return pd.DataFrame()

    storage_df = df[df['series'].str.upper().str.contains('STOCK', na=False)].copy()
    if storage_df.empty:
        return pd.DataFrame()

    pivoted = storage_df.pivot_table(index='date', columns='series_id', values='value')

    # Shift back one day to align with EIA convention
    pivoted.index = pivoted.index - pd.DateOffset(days=1)

    pivoted_reset = pivoted.reset_index()
    date_col_name = pivoted_reset.columns[0]
    pivoted_reset['year'] = pivoted_reset[date_col_name].dt.year
    pivoted_reset['month'] = pivoted_reset[date_col_name].dt.month

    max_dates = pivoted_reset.groupby(['year', 'month'])[date_col_name].max().reset_index()
    max_dates.columns = ['year', 'month', 'max_date']
    max_dates['month_start'] = pd.to_datetime(max_dates[['year', 'month']].assign(day=1))
    max_dates['next_week'] = max_dates['max_date'] + pd.DateOffset(days=7)
    max_dates['month_end'] = max_dates['max_date'] + pd.offsets.MonthEnd(0)
    max_dates['days_to_end'] = (max_dates['month_end'] - max_dates['max_date']).dt.days
    max_dates['ratio'] = max_dates['days_to_end'].clip(upper=7) / 7.0

    result_list = []
    for _, row in max_dates.iterrows():
        max_date = row['max_date']
        next_week = row['next_week']
        ratio = row['ratio']
        month_start = row['month_start']

        if max_date in pivoted.index:
            max_values = pivoted.loc[max_date]
            if ratio > 0 and next_week in pivoted.index:
                next_values = pivoted.loc[next_week]
                weekly_diff = next_values - max_values
                interpolated = max_values + (weekly_diff * ratio)
            else:
                interpolated = max_values

            month_df = interpolated.to_frame().T
            month_df.index = [month_start]
            result_list.append(month_df)

    if result_list:
        monthly_storage = pd.concat(result_list)
        monthly_storage.index.name = 'period'
        monthly_storage = monthly_storage.reset_index()
        monthly_storage = monthly_storage.melt(
            id_vars=['period'], var_name='series_id', value_name='value'
        )
        return monthly_storage

    return pd.DataFrame()


def process_flow_items(df):
    """Process flow items (non-storage) - take average of month."""
    if df.empty:
        return pd.DataFrame()

    flow_df = df[~df['series'].str.upper().str.contains('STOCK', na=False)].copy()
    if flow_df.empty:
        return pd.DataFrame()

    pivoted = flow_df.pivot_table(index='date', columns='series_id', values='value')

    # Shift back one day to align with EIA convention
    pivoted.index = pivoted.index - pd.DateOffset(days=1)

    # Resample to daily, forward fill, then take monthly average
    daily = pivoted.resample('D').last().bfill()
    monthly_flow = daily.resample('ME').mean()

    # Shift to beginning of month
    monthly_flow.index = monthly_flow.index - pd.offsets.MonthBegin(1)

    monthly_flow = monthly_flow.reset_index()
    date_col_name = monthly_flow.columns[0]
    monthly_flow.rename(columns={date_col_name: 'period'}, inplace=True)

    monthly_flow = monthly_flow.melt(
        id_vars=['period'], var_name='series_id', value_name='value'
    )
    monthly_flow['value'] = monthly_flow['value'].round(2)

    return monthly_flow


def compute_derived_series(df):
    """Compute derived series (feedstock runs, P2E stocks, adjustment factor)
    and append to the DataFrame. Same logic as generate_report.py."""

    pivot = df.pivot_table(index="date", columns="series_id", values="value")
    new_rows = []

    # Feedstock Runs = Gross Runs - Crude Runs
    feedstock_pairs = {
        "feedstockRunsUS":  ("WGIRIUS2",  "WCRRIUS2"),
        "feddStockRunsP1":  ("WGIRIP12",  "WCRRIP12"),
        "feedstockRunsP2":  ("WGIRIP22",  "WCRRIP22"),
        "feedstockRunsP3":  ("WGIRIP32",  "WCRRIP32"),
        "feedstockRunsP4":  ("WGIRIP42",  "WCRRIP42"),
        "feedstockRunsP5":  ("WGIRIP52",  "WCRRIP52"),
        # P2E Stocks = P2 - Cushing
        "crudeStocksP2E":   ("WCESTP21",  "W_EPC0_SAX_YCUOK_MBBL"),
    }

    for derived_id, (a, b) in feedstock_pairs.items():
        if a in pivot.columns and b in pivot.columns:
            result = pivot[a] - pivot[b]
            for date, value in result.dropna().items():
                new_rows.append({"date": date, "series_id": derived_id, "value": value, "series": "", "source": ""})

    # Adjustment factor
    adj_cols = ["WCRFPUS2", "WCEIMUS2", "WCRRIUS2", "WCREXUS2", "WCRSTUS1"]
    if all(c in pivot.columns for c in adj_cols):
        stock_change = pivot["WCRSTUS1"].diff() / 7
        adjustment = -(pivot["WCRFPUS2"] + pivot["WCEIMUS2"] - pivot["WCRRIUS2"] - pivot["WCREXUS2"] - stock_change)
        for date, value in adjustment.dropna().items():
            new_rows.append({"date": date, "series_id": "crudeOriginalAdjustment", "value": value, "series": "", "source": ""})

    if new_rows:
        derived_df = pd.DataFrame(new_rows)
        derived_df["date"] = pd.to_datetime(derived_df["date"])
        return pd.concat([df, derived_df], ignore_index=True)
    return df


def create_monthly_data():
    """Create monthly aggregated data from weekly WPS data."""
    logger.info("Loading weekly data...")
    df = load_wps_data()

    logger.info("Computing derived series...")
    df = compute_derived_series(df)

    logger.info("Processing storage items (stocks)...")
    storage_monthly = process_storage_items(df)

    logger.info("Processing flow items (non-stocks)...")
    flow_monthly = process_flow_items(df)

    monthly_df = pd.concat([storage_monthly, flow_monthly], ignore_index=True)

    # Add _plm suffix to series_ids
    monthly_df['series_id'] = monthly_df['series_id'] + '_plm'

    # Format period as date string
    monthly_df['date'] = monthly_df['period'].dt.strftime('%Y-%m-01')

    # Keep lean columns
    monthly_df = monthly_df[['date', 'series_id', 'value']].copy()

    # Drop NA
    rows_before = len(monthly_df)
    monthly_df = monthly_df.dropna(subset=['value'])
    rows_after = len(monthly_df)
    if rows_before > rows_after:
        logger.info(f"  Removed {rows_before - rows_after:,} monthly rows with NA values")

    monthly_df = monthly_df.sort_values(['date', 'series_id'])
    return monthly_df


def create_pivot(df, date_col, index_col, freq_label):
    """Create a pivot table with dates as columns.

    Args:
        df: DataFrame with date_col, index_col, and 'value' columns
        date_col: name of the date column
        index_col: name of the index column (e.g. 'series_id')
        freq_label: label for logging
    """
    pivot_df = df.copy()
    pivot_df[date_col] = pd.to_datetime(pivot_df[date_col])

    pivoted = pivot_df.pivot_table(
        index=index_col,
        columns=date_col,
        values='value'
    )

    pivoted = pivoted.reset_index()

    # Format date columns as strings and sort chronologically
    date_cols = []
    meta_cols = []
    for col in pivoted.columns:
        if isinstance(col, pd.Timestamp):
            date_cols.append((col, col.strftime('%Y-%m-%d')))
        else:
            meta_cols.append(col)

    date_cols.sort(key=lambda x: x[0])

    for timestamp_col, str_col in date_cols:
        if isinstance(timestamp_col, pd.Timestamp) and timestamp_col in pivoted.columns:
            pivoted.rename(columns={timestamp_col: str_col}, inplace=True)

    ordered_cols = meta_cols + [str_col for _, str_col in date_cols]
    pivoted = pivoted[ordered_cols]

    return pivoted


def create_weekly_pivot():
    """Create weekly pivot table from WPS data."""
    logger.info("Creating weekly pivot table...")
    df = load_wps_data()
    return create_pivot(df, 'date', 'series_id', 'weekly')


def main():
    """Main processing function."""
    output_dir = OUTPUT_DIRECTORY_FOR_ADDITIONAL_FILES
    os.makedirs(output_dir, exist_ok=True)

    # Weekly pivot
    logger.info("Creating weekly pivot table...")
    weekly_pivot = create_weekly_pivot()
    weekly_pivot.to_csv(WPS_WEEKLY_PIVOT_FILE, index=False)
    logger.info(f"  Saved weekly pivot with {len(weekly_pivot)} series to {WPS_WEEKLY_PIVOT_FILE}")

    # Monthly aggregation
    logger.info("Creating monthly aggregation...")
    monthly_df = create_monthly_data()
    monthly_df.to_parquet(WPS_MONTHLY_FILE, engine="pyarrow", compression="gzip", index=False)
    logger.info(f"  Saved {len(monthly_df)} rows to {WPS_MONTHLY_FILE}")

    # Monthly pivot
    logger.info("Creating monthly pivot table...")
    monthly_pivot = create_pivot(monthly_df, 'date', 'series_id', 'monthly')
    monthly_pivot.to_csv(WPS_MONTHLY_PIVOT_FILE, index=False)
    logger.info(f"  Saved pivot with {len(monthly_pivot)} series to {WPS_MONTHLY_PIVOT_FILE}")

    logger.info("Processing complete!")
    logger.info(f"Files saved to {OUTPUT_DIRECTORY_FOR_ADDITIONAL_FILES}/")


if __name__ == '__main__':
    main()
