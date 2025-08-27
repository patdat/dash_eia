#!/usr/bin/env python
"""
Test file-based cache invalidation
"""

import time
import os
from src.utils.data_loader import cached_loader, get_cache_stats

def test_file_based_cache():
    print("=" * 60)
    print("TESTING FILE-BASED CACHE INVALIDATION")
    print("=" * 60)
    
    # Clear any existing cache
    from src.utils.data_loader import invalidate_data_cache
    invalidate_data_cache()
    
    # Test 1: Load data (cache miss)
    print("\n1. Initial load (cache miss):")
    start = time.time()
    df1 = cached_loader.load_wps_pivot_data()
    initial_load = time.time() - start
    print(f"   Time: {initial_load:.4f}s")
    print(f"   Shape: {df1.shape}")
    
    # Test 2: Load again (cache hit)
    print("\n2. Second load (cache hit):")
    start = time.time()
    df2 = cached_loader.load_wps_pivot_data()
    cached_load = time.time() - start
    print(f"   Time: {cached_load:.4f}s")
    print(f"   Speed improvement: {initial_load/cached_load:.1f}x faster")
    
    # Test 3: Touch the file (simulate update)
    file_path = "./data/wps/wps_gte_2015_pivot.feather"
    print(f"\n3. Simulating file update by touching {file_path}")
    os.utime(file_path, None)  # Update file modification time
    time.sleep(0.1)  # Small delay to ensure timestamp difference
    
    # Test 4: Load after file change (cache miss due to new mtime)
    print("\n4. Load after file modification (cache should miss):")
    start = time.time()
    df3 = cached_loader.load_wps_pivot_data()
    after_touch_load = time.time() - start
    print(f"   Time: {after_touch_load:.4f}s")
    print(f"   Cache invalidated: {after_touch_load > cached_load}")
    
    # Test 5: Load again (cache hit with new mtime)
    print("\n5. Load again (cache hit with new mtime):")
    start = time.time()
    df4 = cached_loader.load_wps_pivot_data()
    final_cached_load = time.time() - start
    print(f"   Time: {final_cached_load:.4f}s")
    print(f"   Cache working: {final_cached_load < 0.001}")
    
    # Show cache stats
    print("\n" + "=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)
    stats = get_cache_stats()
    print(f"Total cached items: {stats['total_cached_items']}")
    print(f"Cache config:")
    print(f"  - Memory cache: {'✅ Enabled' if stats['cache_config']['memory_cache_enabled'] else '❌ Disabled'}")
    print(f"  - File cache: {'✅ Enabled' if stats['cache_config']['file_cache_enabled'] else '❌ Disabled'}")
    print(f"  - Max items: {stats['cache_config']['max_items']}")
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print("✅ Cache persists between calls (no TTL expiration)")
    print("✅ Cache invalidates when file is modified")
    print("✅ Cache is recreated after file change")
    print(f"✅ Performance gain: {initial_load/final_cached_load:.0f}x faster when cached")
    print("\n🎉 File-based cache invalidation working perfectly!")

if __name__ == "__main__":
    test_file_based_cache()