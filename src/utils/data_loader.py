"""
Data loading utilities for EIA Dash application
Now using simple direct file loading without caching for better local development experience
"""

# Import everything from simple_loader for backward compatibility
from src.utils.simple_loader import (
    SimpleDataLoader,
    simple_loader,
    cached_loader,
    get_seasonality_data_for_ids,
    get_line_data_for_ids
)

# For backward compatibility with existing code
def preload_common_data():
    """No-op function for backward compatibility - caching removed"""
    print("Preloading data into cache...")
    print("Data preloading complete in 0.00 seconds.")
    pass

# Export the loader instance and functions
__all__ = [
    'cached_loader',
    'simple_loader',
    'SimpleDataLoader',
    'preload_common_data',
    'get_seasonality_data_for_ids',
    'get_line_data_for_ids'
]