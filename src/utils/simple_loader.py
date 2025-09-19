"""
Simple data loading utilities without caching for EIA Dash application
Direct file loading for local development - no caching overhead
"""
import pandas as pd
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SimpleDataLoader:
    """Direct data loader without caching - perfect for local development"""

    def __init__(self):
        self.data_dir = "./data"
        self.lookup_dir = "./lookup"

    def load_wps_pivot_data(self) -> pd.DataFrame:
        """Load main WPS pivot data"""
        file_path = f"{self.data_dir}/wps/wps_gte_2015_pivot.feather"
        df = pd.read_feather(file_path)
        df["period"] = pd.to_datetime(df["period"])
        return df

    def load_wps_data(self) -> pd.DataFrame:
        """Load WPS data"""
        file_path = f"{self.data_dir}/wps/wps_gte_2015.feather"
        df = pd.read_feather(file_path)
        df["period"] = pd.to_datetime(df["period"])
        return df

    def load_seasonality_data(self) -> pd.DataFrame:
        """Load seasonality data"""
        file_path = f"{self.data_dir}/wps/seasonality_data.feather"
        return pd.read_feather(file_path)

    def load_line_data(self) -> pd.DataFrame:
        """Load line graph data"""
        file_path = f"{self.data_dir}/wps/graph_line_data.feather"
        df = pd.read_feather(file_path)
        df["period"] = pd.to_datetime(df["period"])
        return df

    def load_steo_pivot_data(self) -> pd.DataFrame:
        """Load STEO pivot data"""
        file_path = f"{self.data_dir}/steo/steo_pivot.feather"
        return pd.read_feather(file_path)

    def load_steo_dpr_data(self) -> pd.DataFrame:
        """Load STEO DPR data"""
        file_path = f"{self.data_dir}/steo/steo_pivot_dpr.feather"
        return pd.read_feather(file_path)

    def load_steo_dpr_other_data(self) -> pd.DataFrame:
        """Load STEO DPR Other data"""
        file_path = f"{self.data_dir}/steo/steo_pivot_dpr_other.feather"
        return pd.read_feather(file_path)

    def load_cli_data(self) -> pd.DataFrame:
        """Load Company Level Imports data"""
        file_path = f"{self.data_dir}/cli/companylevelimports.parquet"
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return pd.DataFrame()

    def load_cli_crude_data(self) -> pd.DataFrame:
        """Load Company Level Crude Imports data"""
        file_path = f"{self.data_dir}/cli/companylevelimports_crude.parquet"
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return pd.DataFrame()

    def load_dpr_mapping(self) -> pd.DataFrame:
        """Load DPR mapping"""
        return pd.read_csv(f"{self.lookup_dir}/steo/mapping_dpr.csv")

    def load_steo_mapping(self) -> pd.DataFrame:
        """Load STEO mapping"""
        return pd.read_csv(f"{self.lookup_dir}/steo/mapping.csv")

    def load_dpr_other_mapping(self) -> pd.DataFrame:
        """Load DPR Other mapping"""
        return pd.read_csv(f"{self.lookup_dir}/steo/mapping_dpr_other.csv")

    def load_production_mapping(self) -> dict:
        """Load production mapping"""
        from src.wps.mapping import production_mapping
        return production_mapping

    def load_ag_mapping(self) -> dict:
        """Load AG grid mapping"""
        from src.wps.ag_mapping import ag_mapping
        return ag_mapping

    def get_filtered_data(self, data_name: str, start_date: str = None) -> pd.DataFrame:
        """Load and filter data by date if specified"""
        if data_name == "wps_pivot":
            df = self.load_wps_pivot_data()
            if start_date:
                df = df[df["period"] >= pd.to_datetime(start_date)]
            return df
        elif data_name == "wps":
            df = self.load_wps_data()
            if start_date:
                df = df[df["period"] >= pd.to_datetime(start_date)]
            return df
        else:
            raise ValueError(f"Unknown data name: {data_name}")

    def load_processed_dpr_data(self, region=None) -> pd.DataFrame:
        """Process DPR data for a specific region or all regions"""
        start_time = datetime.now()

        # Load base data
        df = self.load_steo_dpr_data()
        mapping_df = self.load_dpr_mapping()

        # Get actual metadata columns from the dataframe
        metadata_cols = ['id', 'name', 'release_date', 'uom']
        date_columns = [col for col in df.columns if col not in metadata_cols]

        # Melt the dataframe
        df_melted = pd.melt(df,
                           id_vars=metadata_cols,
                           value_vars=date_columns,
                           var_name='delivery_month',
                           value_name='value')

        # Convert to datetime
        df_melted['delivery_month'] = pd.to_datetime(df_melted['delivery_month'])

        # Merge with mapping
        df_melted = df_melted.merge(mapping_df[['id', 'region']], on='id', how='left')

        # Filter by region if specified
        if region:
            df_melted = df_melted[df_melted['region'] == region]

        # Log processing time
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processed DPR data for region={region} in {elapsed:.3f}s")

        return df_melted


# Create a single instance to use throughout the app
simple_loader = SimpleDataLoader()

# For backward compatibility - apps can import either name
cached_loader = simple_loader


# Standalone functions for specific data filtering
def get_seasonality_data_for_ids(id_list: tuple) -> pd.DataFrame:
    """Get seasonality data for specific IDs"""
    df = simple_loader.load_seasonality_data()
    return df[df["id"].isin(list(id_list))]


def get_line_data_for_ids(id_list: tuple) -> pd.DataFrame:
    """Get line data for specific IDs"""
    df = simple_loader.load_line_data()
    return df[["period"] + list(id_list)]