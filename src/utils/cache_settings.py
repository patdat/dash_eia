"""
Cache configuration settings
"""
import os

# Cache settings
CACHE_CONFIG = {
    # Default TTL (time to live) in seconds
    'DEFAULT_TTL': int(os.getenv('CACHE_DEFAULT_TTL', '3600')),  # 1 hour
    
    # Data-specific TTL settings
    'DATA_TTL': {
        'wps_data': int(os.getenv('CACHE_WPS_TTL', '3600')),     # 1 hour
        'mapping_data': int(os.getenv('CACHE_MAPPING_TTL', '7200')), # 2 hours
        'steo_data': int(os.getenv('CACHE_STEO_TTL', '3600')),   # 1 hour
        'seasonality_data': int(os.getenv('CACHE_SEASONALITY_TTL', '1800')), # 30 minutes
        'line_data': int(os.getenv('CACHE_LINE_TTL', '1800')),   # 30 minutes
    },
    
    # Enable/disable caching
    'ENABLE_MEMORY_CACHE': os.getenv('ENABLE_MEMORY_CACHE', 'true').lower() == 'true',
    'ENABLE_FILE_CACHE': os.getenv('ENABLE_FILE_CACHE', 'false').lower() == 'true',
    
    # Preload settings
    'PRELOAD_ON_STARTUP': os.getenv('PRELOAD_CACHE', 'true').lower() == 'true',
    
    # Cache directory for file caching
    'CACHE_DIR': os.getenv('CACHE_DIR', './cache'),
    
    # Max memory cache items (LRU eviction)
    'MAX_CACHE_ITEMS': int(os.getenv('MAX_CACHE_ITEMS', '100')),
}
