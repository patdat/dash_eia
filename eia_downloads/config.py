from pathlib import Path

DATA_DIR = Path("./data")
LOOKUP_DIR = Path(__file__).parent / "lookup"


def get_data_path(module, filename):
    """Returns DATA_DIR / module / filename, auto-creates parent dirs."""
    path = DATA_DIR / module / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_lookup_path(*parts):
    """Returns LOOKUP_DIR / parts."""
    return LOOKUP_DIR.joinpath(*parts)


def set_data_dir(path):
    """Runtime override for output location."""
    global DATA_DIR
    DATA_DIR = Path(path)
