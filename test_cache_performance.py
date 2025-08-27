#!/usr/bin/env python
"""
Cache Performance Benchmark Script
Tests the performance improvements from the new caching system
"""

import time
import pandas as pd
from src.utils.data_loader import cached_loader, get_cache_stats

def benchmark_direct_reads():
    """Benchmark direct file reads (old method)"""
    print("\n=== DIRECT FILE READS (Old Method) ===")
    times = []
    
    for i in range(5):
        start = time.time()
        
        # Simulate what pages used to do
        df1 = pd.read_feather('data/wps/wps_gte_2015_pivot.feather')
        df2 = pd.read_feather('data/wps/seasonality_data.feather')
        df3 = pd.read_feather('data/steo/steo_pivot_dpr.feather')
        df4 = pd.read_csv('lookup/steo/mapping_dpr.csv')
        
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.3f}s")
    
    avg_time = sum(times) / len(times)
    print(f"  Average: {avg_time:.3f}s")
    return avg_time

def benchmark_cached_reads():
    """Benchmark cached reads (new method)"""
    print("\n=== CACHED READS (New Method) ===")
    times = []
    
    # First run to warm up cache
    cached_loader.load_wps_pivot_data()
    cached_loader.load_seasonality_data()
    cached_loader.load_steo_dpr_data()
    cached_loader.load_dpr_mapping()
    
    for i in range(5):
        start = time.time()
        
        # Use cached loader
        df1 = cached_loader.load_wps_pivot_data()
        df2 = cached_loader.load_seasonality_data()
        df3 = cached_loader.load_steo_dpr_data()
        df4 = cached_loader.load_dpr_mapping()
        
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.3f}s")
    
    avg_time = sum(times) / len(times)
    print(f"  Average: {avg_time:.3f}s")
    return avg_time

def main():
    print("=" * 50)
    print("CACHE PERFORMANCE BENCHMARK")
    print("=" * 50)
    
    # Run benchmarks
    direct_time = benchmark_direct_reads()
    cached_time = benchmark_cached_reads()
    
    # Calculate improvements
    improvement = direct_time / cached_time
    time_saved = direct_time - cached_time
    percent_faster = ((direct_time - cached_time) / direct_time) * 100
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Direct reads: {direct_time:.3f}s")
    print(f"Cached reads: {cached_time:.3f}s")
    print(f"")
    print(f"🚀 Performance improvement: {improvement:.1f}x faster")
    print(f"⏱️  Time saved per request: {time_saved:.3f}s")
    print(f"📈 Percent improvement: {percent_faster:.1f}%")
    
    # Show cache stats
    stats = get_cache_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"  - Total cached items: {stats['total_cached_items']}")
    print(f"  - Hit rate: {stats['cache_performance']['hit_rate']:.1%}")
    print(f"  - Memory cache: {'✅ Enabled' if stats['cache_config']['memory_cache_enabled'] else '❌ Disabled'}")
    print(f"  - File cache: {'✅ Enabled' if stats['cache_config']['file_cache_enabled'] else '❌ Disabled'}")
    print(f"  - Max cache items: {stats['cache_config']['max_items']}")
    
    print("\n✨ Cache optimization complete!")

if __name__ == "__main__":
    main()