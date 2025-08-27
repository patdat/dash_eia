#!/usr/bin/env python3
"""
Cache management command-line tool
Usage: python -m src.utils.cache_cli_tool [command]

Commands:
  refresh    - Refresh all cached data
  clear      - Clear all cache
  stats      - Show cache statistics
  check      - Check data file freshness
"""
import sys
import os

from src.utils.data_loader import (
    refresh_data_and_cache, 
    invalidate_data_cache, 
    get_cache_stats, 
    check_data_freshness,
    auto_refresh_if_needed
)


def show_stats():
    """Show cache and data file statistics"""
    stats = get_cache_stats()
    print(f"Cache Statistics:")
    print(f"  Total cached items: {stats['total_cached_items']}")
    print(f"  Cache keys: {stats['cache_keys'][:5]}{'...' if len(stats['cache_keys']) > 5 else ''}")
    
    print(f"\nData Files:")
    for file_path, info in stats['data_files'].items():
        if info['exists']:
            print(f"  ✅ {file_path} (last modified: {info['last_modified']})")
        else:
            print(f"  ❌ {file_path} (not found)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "refresh":
        print("Refreshing all cached data...")
        refresh_data_and_cache()
        print("✅ Cache refreshed successfully!")
        
    elif command == "clear":
        print("Clearing all cache...")
        invalidate_data_cache()
        print("✅ Cache cleared successfully!")
        
    elif command == "stats":
        show_stats()
        
    elif command == "check":
        print("Checking data file freshness...")
        file_info = check_data_freshness()
        for file_path, info in file_info.items():
            if info['exists']:
                print(f"✅ {file_path} - {info['last_modified']}")
            else:
                print(f"❌ {file_path} - Not found")
        
        # Check if auto-refresh is needed
        if auto_refresh_if_needed():
            print("🔄 Cache was auto-refreshed due to recent data updates")
        else:
            print("💾 Cache is up to date")
            
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
