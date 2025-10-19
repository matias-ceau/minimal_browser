import json
from pathlib import Path

DATA_DIR = Path.home() / ".minimal_browser/data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_dir(directory: Path) -> None:
    """Ensure that a directory exists."""
    directory.mkdir(parents=True, exist_ok=True)


def read_json(file_path: Path):
    """Read a JSON file and return the contents."""
    with open(file_path, "r") as f:
        return json.load(f)


def write_json(file_path: Path, data) -> None:
    """Write data to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def storage_path(filename: str) -> Path:
    """Get the full path to a storage file."""
    return DATA_DIR / filename
