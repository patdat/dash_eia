"""
Caching utilities for EIA Dash application
"""
import functools
import pandas as pd
import os
from datetime import datetime, timedelta
import pickle
import hashlib
from typing import Optional, Any, Dict


class DataCache:
    """Simple in-memory cache for application data"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._ttl = {}  # Time to live for each cached item
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if it exists and hasn't expired"""
        if key not in self._cache:
            return None
            
        # Check if item has expired
        if key in self._ttl:
            if datetime.now() > self._timestamps[key] + self._ttl[key]:
                self.invalidate(key)
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set item in cache with optional TTL"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        
        if ttl_seconds:
            self._ttl[key] = timedelta(seconds=ttl_seconds)
    
    def invalidate(self, key: str):
        """Remove item from cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._ttl.pop(key, None)
    
    def clear(self):
        """Clear all cached data"""
        self._cache.clear()
        self._timestamps.clear()
        self._ttl.clear()
    
    def keys(self):
        """Get all cache keys"""
        return list(self._cache.keys())


# Global cache instance
app_cache = DataCache()


def file_based_cache(file_path: str, ttl_seconds: int = 3600):
    """
    Decorator for caching function results to disk
    Useful for expensive data processing operations
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            cache_file = f"{file_path}_{cache_key}.pkl"
            
            # Check if cache file exists and is recent
            if os.path.exists(cache_file):
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                if file_age.total_seconds() < ttl_seconds:
                    try:
                        with open(cache_file, 'rb') as f:
                            return pickle.load(f)
                    except:
                        # If loading fails, delete corrupt cache file
                        os.remove(cache_file)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Save to cache file
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
            except Exception as e:
                print(f"Failed to cache result to {cache_file}: {e}")
            
            return result
        return wrapper
    return decorator


def memory_cache(ttl_seconds: int = None, file_dependency: str = None):
    """
    Decorator for caching function results in memory.
    If file_dependency is provided, cache invalidates when file changes.
    Otherwise uses TTL (defaults to forever if not specified).
    """
    def decorator(func):
        cache_key_base = func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Include file modification time in cache key if file_dependency provided
            if file_dependency and os.path.exists(file_dependency):
                file_mtime = os.path.getmtime(file_dependency)
                cache_key = f"{cache_key_base}_{file_mtime}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            else:
                cache_key = f"{cache_key_base}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = app_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            # Use provided TTL or default to forever (1 year)
            actual_ttl = ttl_seconds if ttl_seconds is not None else 31536000
            app_cache.set(cache_key, result, actual_ttl)
            
            return result
        return wrapper
    return decorator


def get_file_hash(file_path: str) -> str:
    """Get hash of file content for cache invalidation"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    except:
        return ""


def smart_file_cache(file_dependencies: list, ttl_seconds: int = 3600):
    """
    Cache that invalidates when dependent files change
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key including file hashes
            file_hashes = [get_file_hash(f) for f in file_dependencies if os.path.exists(f)]
            cache_key = f"{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items()) + tuple(file_hashes)).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = app_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            app_cache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator
