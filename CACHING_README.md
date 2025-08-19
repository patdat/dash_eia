# EIA Dashboard Caching Implementation

## Overview

This implementation adds comprehensive caching to your EIA Dashboard to significantly improve performance, especially for the initial load and chart generation.

## Features

### 1. Multi-Level Caching
- **Memory Cache**: Fast in-memory caching for frequently accessed data
- **File Cache**: Persistent disk-based caching for expensive operations
- **Smart Cache Invalidation**: Automatic cache invalidation when source files change

### 2. Cached Data Types
- WPS pivot data (main dataset)
- Seasonality data for charts
- Line graph data
- Mapping data (production, AG grid)
- STEO/DPR data
- Filtered/processed datasets

### 3. Performance Optimizations
- Data preloading on application startup
- Lazy loading with caching
- Efficient data filtering with cache
- Reduced file I/O operations

## Usage

### Basic Usage
The caching system is automatically enabled. No code changes needed in your existing pages.

### Environment Variables
Control caching behavior with environment variables:

```bash
# Enable/disable caching
ENABLE_MEMORY_CACHE=true
ENABLE_FILE_CACHE=false
PRELOAD_CACHE=true

# Cache TTL (time to live) in seconds
CACHE_DEFAULT_TTL=3600
CACHE_WPS_TTL=3600
CACHE_MAPPING_TTL=7200
CACHE_SEASONALITY_TTL=1800

# Cache limits
MAX_CACHE_ITEMS=100
CACHE_DIR=./cache
```

### Manual Cache Management
```python
from utils.data_loader import cached_loader
from utils.cache import app_cache

# Clear all cache
app_cache.clear()

# Invalidate specific cache pattern
cached_loader.invalidate_cache("wps")

# Preload common data
from utils.data_loader import preload_common_data
preload_common_data()

# Get cache statistics
from utils.data_loader import get_cache_stats
stats = get_cache_stats()
```

## Files Added/Modified

### New Files
- `utils/cache.py` - Core caching utilities
- `utils/data_loader.py` - Cached data loading functions
- `utils/cache_config.py` - Cache configuration
- `pages/cache_management.py` - Optional cache management UI

### Modified Files
- `app.py` - Updated to use cached data loader
- `utils_wps/calculation.py` - Uses cached data functions
- `utils_wps/ag_calculations.py` - Uses cached data loader
- `index.py` - Added cache preloading

## Performance Impact

### Before Caching
- Each page load: Multiple file reads from disk
- Each chart: Re-processing of raw data
- Callback execution: Repeated data loading

### After Caching
- First load: Data loaded once and cached
- Subsequent loads: Data served from memory
- Chart generation: Pre-processed data ready
- Callbacks: Cached filtered datasets

### Expected Improvements
- **Initial load time**: 50-70% reduction
- **Chart generation**: 60-80% faster
- **Memory usage**: Slightly higher (cached data)
- **CPU usage**: Reduced processing overhead

## Monitoring

### Cache Statistics
```python
from utils.data_loader import get_cache_stats
stats = get_cache_stats()
print(f"Cached items: {stats['total_cached_items']}")
```

### Cache Management UI
Optionally add cache management page to your navigation:
```python
# In index.py navigation
dbc.NavLink("Cache Management", href="/cache-management", active="exact", className="nav-link")

# In routing callback
elif pathname == '/cache-management':
    from pages.cache_management import cache_management_layout
    return cache_management_layout
```

## Best Practices

### 1. Cache Key Design
- Use consistent naming patterns
- Include relevant parameters in keys
- Consider data dependencies

### 2. TTL Management
- Short TTL for frequently changing data
- Long TTL for static/mapping data
- Balance between freshness and performance

### 3. Memory Management
- Monitor cache memory usage
- Use LRU eviction for large datasets
- Clear cache periodically in production

### 4. Error Handling
- Graceful fallbacks when cache fails
- Log cache hits/misses for monitoring
- Invalidate corrupt cache entries

## Troubleshooting

### Cache Not Working
1. Check environment variables
2. Verify file permissions for cache directory
3. Monitor memory usage
4. Check for import errors

### Memory Issues
1. Reduce cache TTL values
2. Lower MAX_CACHE_ITEMS
3. Clear cache more frequently
4. Disable file caching if not needed

### Performance Not Improved
1. Verify cache is being used (check stats)
2. Ensure data preloading is working
3. Check if cache keys are consistent
4. Monitor cache hit rates

## Advanced Configuration

### Custom Cache Decorators
```python
from utils.cache import memory_cache, file_based_cache

@memory_cache(ttl_seconds=1800)
def expensive_calculation(data):
    # Your expensive operation
    return processed_data

@file_based_cache("./cache/custom", ttl_seconds=7200)
def file_processing():
    # File processing that can be cached to disk
    return result
```

### Dynamic Cache Invalidation
```python
# Invalidate cache when source data changes
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CacheInvalidator(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.feather'):
            # Invalidate related cache
            cached_loader.invalidate_cache("data")
```

## Production Deployment

### Docker Environment Variables
```dockerfile
ENV ENABLE_MEMORY_CACHE=true
ENV PRELOAD_CACHE=true
ENV CACHE_DEFAULT_TTL=3600
ENV MAX_CACHE_ITEMS=200
```

### Kubernetes Configuration
```yaml
env:
  - name: ENABLE_MEMORY_CACHE
    value: "true"
  - name: PRELOAD_CACHE
    value: "true"
  - name: CACHE_DEFAULT_TTL
    value: "3600"
```

This caching implementation should significantly improve your dashboard's performance, especially for the initial load and chart generation that you mentioned was slow.
