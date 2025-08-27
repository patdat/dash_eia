"""
Cache configuration settings - File-based invalidation only
"""
import os

# Cache settings
CACHE_CONFIG = {
    # Default TTL - Set to infinity (cache forever until file changes)
    'DEFAULT_TTL': int(os.getenv('CACHE_DEFAULT_TTL', '31536000')),  # 1 year (effectively forever)
    
    # Data-specific TTL settings - All set to persist until file changes
    'DATA_TTL': {
        'wps_data': int(os.getenv('CACHE_WPS_TTL', '31536000')),     # Forever
        'mapping_data': int(os.getenv('CACHE_MAPPING_TTL', '31536000')), # Forever
        'steo_data': int(os.getenv('CACHE_STEO_TTL', '31536000')),   # Forever
        'seasonality_data': int(os.getenv('CACHE_SEASONALITY_TTL', '31536000')), # Forever
        'line_data': int(os.getenv('CACHE_LINE_TTL', '31536000')),   # Forever
        'cli_data': int(os.getenv('CACHE_CLI_TTL', '31536000')),     # Forever
        'dpr_data': int(os.getenv('CACHE_DPR_TTL', '31536000')),     # Forever
        'processed_data': int(os.getenv('CACHE_PROCESSED_TTL', '31536000')), # Forever
    },
    
    # Enable/disable caching - ENABLE FILE CACHE FOR PERFORMANCE
    'ENABLE_MEMORY_CACHE': os.getenv('ENABLE_MEMORY_CACHE', 'true').lower() == 'true',
    'ENABLE_FILE_CACHE': os.getenv('ENABLE_FILE_CACHE', 'true').lower() == 'true',  # ENABLED!
    
    # Preload settings
    'PRELOAD_ON_STARTUP': os.getenv('PRELOAD_CACHE', 'true').lower() == 'true',
    
    # Cache directory for file caching
    'CACHE_DIR': os.getenv('CACHE_DIR', './cache'),
    
    # Max memory cache items - Increased for better performance
    'MAX_CACHE_ITEMS': int(os.getenv('MAX_CACHE_ITEMS', '500')),  # Increased from 100
    
    # New performance settings
    'FILE_CACHE_THRESHOLD_MB': float(os.getenv('FILE_CACHE_THRESHOLD_MB', '10')),  # Use file cache for data > 10MB
    'ENABLE_CACHE_METRICS': os.getenv('ENABLE_CACHE_METRICS', 'true').lower() == 'true',  # Track performance
    'CACHE_WARM_UP_PARALLEL': os.getenv('CACHE_WARM_UP_PARALLEL', 'true').lower() == 'true',  # Parallel preload
}
