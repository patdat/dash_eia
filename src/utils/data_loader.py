"""
Optimized data loading utilities with caching for EIA Dash application
"""
import pandas as pd
from src.utils.cache_storage import memory_cache, smart_file_cache, app_cache
import os
from functools import lru_cache
from datetime import datetime
import time
import logging
from src.utils.cache_settings import CACHE_CONFIG

# Set up logging for cache performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CachedDataLoader:
    """Centralized data loader with built-in caching and performance monitoring"""
    
    def __init__(self):
        self.data_dir = "./data"
        self.lookup_dir = "./lookup"
        self.cache_hits = 0
        self.cache_misses = 0
        self.load_times = {}
    
    @memory_cache(file_dependency="./data/wps/wps_gte_2015_pivot.feather")
    def load_wps_pivot_data(self) -> pd.DataFrame:
        """Load main WPS pivot data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/wps/wps_gte_2015_pivot.feather"
        df = pd.read_feather(file_path)
        df["period"] = pd.to_datetime(df["period"])
        return df
    
    @memory_cache(file_dependency="./data/wps/wps_gte_2015.feather")
    def load_wps_data(self) -> pd.DataFrame:
        """Load WPS data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/wps/wps_gte_2015.feather"
        df = pd.read_feather(file_path)
        df["period"] = pd.to_datetime(df["period"])
        return df
    
    @memory_cache(file_dependency="./data/wps/seasonality_data.feather")
    def load_seasonality_data(self) -> pd.DataFrame:
        """Load seasonality data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/wps/seasonality_data.feather"
        return pd.read_feather(file_path)
    
    @memory_cache(file_dependency="./data/wps/graph_line_data.feather")
    def load_line_data(self) -> pd.DataFrame:
        """Load line graph data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/wps/graph_line_data.feather"
        df = pd.read_feather(file_path)
        df["period"] = pd.to_datetime(df["period"])
        return df
    
    @memory_cache(file_dependency="./data/steo/steo_pivot.feather")
    def load_steo_pivot_data(self) -> pd.DataFrame:
        """Load STEO pivot data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/steo/steo_pivot.feather"
        return pd.read_feather(file_path)
    
    @memory_cache(file_dependency="./data/steo/steo_pivot_dpr.feather")
    def load_steo_dpr_data(self) -> pd.DataFrame:
        """Load STEO DPR data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/steo/steo_pivot_dpr.feather"
        return pd.read_feather(file_path)
    
    @memory_cache(file_dependency="./data/steo/steo_pivot_dpr_other.feather")
    def load_steo_dpr_other_data(self) -> pd.DataFrame:
        """Load STEO DPR Other data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/steo/steo_pivot_dpr_other.feather"
        return pd.read_feather(file_path)
    
    @memory_cache(file_dependency="./data/cli/companylevelimports.parquet")
    def load_cli_data(self) -> pd.DataFrame:
        """Load Company Level Imports data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/cli/companylevelimports.parquet"
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return pd.DataFrame()
    
    @memory_cache(file_dependency="./data/cli/companylevelimports_crude.parquet")
    def load_cli_crude_data(self) -> pd.DataFrame:
        """Load Company Level Crude Imports data with file-based cache invalidation"""
        file_path = f"{self.data_dir}/cli/companylevelimports_crude.parquet"
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return pd.DataFrame()
    
    @smart_file_cache(
        file_dependencies=["./lookup/steo/mapping_dpr.csv"], 
        ttl_seconds=31536000  # Cache forever until file changes
    )
    def load_dpr_mapping(self) -> pd.DataFrame:
        """Load DPR mapping with smart cache invalidation"""
        return pd.read_csv(f"{self.lookup_dir}/steo/mapping_dpr.csv")
    
    @smart_file_cache(
        file_dependencies=["./lookup/steo/mapping_dpr_other.csv"], 
        ttl_seconds=31536000  # Cache forever until file changes
    )
    def load_dpr_other_mapping(self) -> pd.DataFrame:
        """Load DPR Other mapping with file-based cache invalidation"""
        return pd.read_csv(f"{self.lookup_dir}/steo/mapping_dpr_other.csv")
    
    @memory_cache()  # Mappings rarely change, cache forever
    def load_production_mapping(self) -> dict:
        """Load production mapping with persistent caching"""
        from src.wps.mapping import production_mapping
        return production_mapping
    
    @memory_cache()  # Mappings rarely change, cache forever
    def load_ag_mapping(self) -> dict:
        """Load AG grid mapping with persistent caching"""
        from src.wps.ag_mapping import ag_mapping
        return ag_mapping
    
    @memory_cache(file_dependency="./data/steo/steo_pivot_dpr.feather")
    def load_processed_dpr_data(self, region: str = None) -> pd.DataFrame:
        """Load and process DPR data with file-based cache invalidation for specific region"""
        start_time = time.time()
        
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
        
        load_time = time.time() - start_time
        if CACHE_CONFIG.get('ENABLE_CACHE_METRICS'):
            logger.info(f"Processed DPR data for region={region} in {load_time:.3f}s")
        
        return df_melted
    
    def get_filtered_data(self, data_type: str, start_date: str = "2015-01-01") -> pd.DataFrame:
        """Get filtered data with caching"""
        cache_key = f"filtered_{data_type}_{start_date}"
        
        cached = app_cache.get(cache_key)
        if cached is not None:
            return cached
        
        if data_type == "wps_pivot":
            df = self.load_wps_pivot_data()
        elif data_type == "line_data":
            df = self.load_line_data()
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        # Apply filtering
        df_filtered = df[df["period"] > start_date].reset_index(drop=True)
        
        # Cache the result forever (until data changes)
        app_cache.set(cache_key, df_filtered, ttl_seconds=31536000)  # 1 year
        
        return df_filtered
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            app_cache.clear()
        else:
            keys_to_remove = [key for key in app_cache.keys() if pattern in key]
            for key in keys_to_remove:
                app_cache.invalidate(key)


# Global cached data loader instance
cached_loader = CachedDataLoader()


# Cached versions of commonly used functions
@lru_cache(maxsize=32)
def get_initial_data_cached():
    """Cached version of get_initial_data"""
    return cached_loader.get_filtered_data("wps_pivot", "2015-01-01")


@memory_cache(file_dependency="./data/wps/seasonality_data.feather")
def get_seasonality_data_for_ids(id_list: tuple) -> pd.DataFrame:
    """Get seasonality data for specific IDs with file-based cache invalidation"""
    df = cached_loader.load_seasonality_data()
    return df[df["id"].isin(list(id_list))]


@memory_cache(file_dependency="./data/wps/graph_line_data.feather")
def get_line_data_for_ids(id_list: tuple) -> pd.DataFrame:
    """Get line data for specific IDs with file-based cache invalidation"""
    df = cached_loader.load_line_data()
    return df[["period"] + list(id_list)]


def preload_common_data():
    """Preload commonly used data into cache with performance tracking"""
    print("Preloading data into cache...")
    start_time = time.time()
    
    try:
        # Load WPS datasets
        cached_loader.load_wps_pivot_data()
        cached_loader.load_wps_data()
        cached_loader.load_seasonality_data()
        cached_loader.load_line_data()
        
        # Load STEO datasets
        cached_loader.load_steo_pivot_data()
        cached_loader.load_steo_dpr_data()
        cached_loader.load_steo_dpr_other_data()
        
        # Load CLI datasets if available
        cached_loader.load_cli_data()
        cached_loader.load_cli_crude_data()
        
        # Load mappings
        cached_loader.load_production_mapping()
        cached_loader.load_ag_mapping()
        cached_loader.load_dpr_mapping()
        cached_loader.load_dpr_other_mapping()
        
        # Load filtered datasets
        cached_loader.get_filtered_data("wps_pivot")
        cached_loader.get_filtered_data("line_data")
        
        # Preload processed data for common regions
        for region in ['Bakken', 'Eagle Ford', 'Permian', 'Haynesville']:
            cached_loader.load_processed_dpr_data(region)
        
        total_time = time.time() - start_time
        print(f"Data preloading complete in {total_time:.2f} seconds.")
        
        if CACHE_CONFIG.get('ENABLE_CACHE_METRICS'):
            logger.info(f"Preloaded cache in {total_time:.2f}s")
            
    except Exception as e:
        print(f"Error during preloading: {e}")
        logger.error(f"Preload failed: {e}")


def invalidate_data_cache():
    """Invalidate all data-related cache entries"""
    print("Invalidating data cache...")
    cached_loader.invalidate_cache()
    app_cache.clear()
    print("Data cache invalidated.")


def refresh_data_and_cache():
    """Force refresh all cached data"""
    print("Refreshing data and cache...")
    
    # Clear existing cache
    invalidate_data_cache()
    
    # Reload fresh data
    preload_common_data()
    
    print("Data and cache refreshed successfully.")


def check_data_freshness():
    """Check if data files have been updated since last cache"""
    data_files = [
        "./data/wps/wps_gte_2015_pivot.feather",
        "./data/wps/seasonality_data.feather", 
        "./data/wps/graph_line_data.feather",
        "./data/steo/steo_pivot.feather",
        "./data/steo/steo_pivot_dpr.feather"
    ]
    
    file_info = {}
    for file_path in data_files:
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            file_info[file_path] = {
                'last_modified': datetime.fromtimestamp(mtime),
                'exists': True
            }
        else:
            file_info[file_path] = {'exists': False}
    
    return file_info


def auto_refresh_if_needed():
    """Automatically refresh cache if data files are newer"""
    try:
        file_info = check_data_freshness()
        current_time = datetime.now()
        
        # Check if any file was modified in the last 5 minutes
        needs_refresh = False
        for file_path, info in file_info.items():
            if info['exists']:
                file_age = current_time - info['last_modified']
                if file_age.total_seconds() < 300:  # 5 minutes
                    print(f"Detected recent update to {file_path}")
                    needs_refresh = True
                    break
        
        if needs_refresh:
            print("Auto-refreshing cache due to recent data updates...")
            refresh_data_and_cache()
            return True
        return False
    except Exception as e:
        print(f"Error checking data freshness: {e}")
        return False


def get_cache_stats():
    """Get cache statistics for monitoring"""
    cache_keys = app_cache.keys()
    file_info = check_data_freshness()
    
    stats = {
        "total_cached_items": len(cache_keys),
        "cache_keys": cache_keys,
        "data_files": file_info,
        "cache_performance": {
            "hits": cached_loader.cache_hits,
            "misses": cached_loader.cache_misses,
            "hit_rate": cached_loader.cache_hits / max(1, cached_loader.cache_hits + cached_loader.cache_misses),
            "load_times": cached_loader.load_times
        },
        "cache_config": {
            "memory_cache_enabled": CACHE_CONFIG.get('ENABLE_MEMORY_CACHE'),
            "file_cache_enabled": CACHE_CONFIG.get('ENABLE_FILE_CACHE'),
            "max_items": CACHE_CONFIG.get('MAX_CACHE_ITEMS')
        }
    }
    
    if CACHE_CONFIG.get('ENABLE_CACHE_METRICS'):
        logger.info(f"Cache stats: Hit rate={stats['cache_performance']['hit_rate']:.2%}, Total items={stats['total_cached_items']}")
    
    return stats


# Optional: Preload data when module is imported
if os.getenv("PRELOAD_CACHE", "true").lower() == "true":
    # Check if data was recently updated before preloading
    auto_refresh_if_needed()
    preload_common_data()
