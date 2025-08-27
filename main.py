from src.wps.download_xlsx import main as download_wps
from src.steo.download import main as download_steo
from src.cli.main import main as download_cli

def main():
    download_wps()
    download_steo()
    download_cli()

if __name__ == "__main__":
    main()    