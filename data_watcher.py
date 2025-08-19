#!/usr/bin/env python3
"""
Data update watcher - monitors data files for changes and refreshes cache
Usage: python data_watcher.py

This script monitors your data files and automatically refreshes the cache when they change.
Useful for development or when you have automated data updates.
"""
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("watchdog not installed. Install with: pip install watchdog")
    sys.exit(1)

from utils.data_loader import refresh_data_and_cache


class DataUpdateHandler(FileSystemEventHandler):
    """Handle file system events for data files"""
    
    def __init__(self):
        super().__init__()
        self.last_refresh = 0
        self.refresh_cooldown = 10  # 10 seconds cooldown between refreshes
        
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
            
        # Only watch .feather and .csv files in data directory
        if not (event.src_path.endswith('.feather') or event.src_path.endswith('.csv')):
            return
            
        if 'data/' not in event.src_path:
            return
            
        current_time = time.time()
        if current_time - self.last_refresh < self.refresh_cooldown:
            return  # Skip if recently refreshed
            
        print(f"Data file updated: {event.src_path}")
        print("Refreshing cache...")
        
        try:
            refresh_data_and_cache()
            self.last_refresh = current_time
            print("✅ Cache refreshed successfully!")
        except Exception as e:
            print(f"❌ Failed to refresh cache: {e}")


def main():
    """Main function to start watching data files"""
    data_dir = Path("./data")
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir.absolute()}")
        sys.exit(1)
    
    print(f"Watching data directory: {data_dir.absolute()}")
    print("Press Ctrl+C to stop")
    
    event_handler = DataUpdateHandler()
    observer = Observer()
    observer.schedule(event_handler, str(data_dir), recursive=True)
    
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping data watcher...")
        observer.stop()
    
    observer.join()
    print("Data watcher stopped.")


if __name__ == "__main__":
    main()
