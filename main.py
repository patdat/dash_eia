from src.wps.download_xlsx import main as download_wps
from src.steo.download import main as download_steo
from src.cli.main import main as download_cli

def main():
    """Update all data sources and refresh cache"""
    print("=" * 50)
    print("Starting full data update...")
    print("=" * 50)
    
    # Download all data
    download_wps()
    download_steo()
    download_cli()
    
    # Ensure cache is refreshed with new data
    try:
        from src.utils.data_loader import refresh_data_and_cache
        print("\n" + "=" * 50)
        print("Refreshing cache with new data...")
        print("=" * 50)
        refresh_data_and_cache()
        print("\n✅ All data updated and cache refreshed!")
    except Exception as e:
        print(f"Cache refresh notice: {e}")

if __name__ == "__main__":
    main()    