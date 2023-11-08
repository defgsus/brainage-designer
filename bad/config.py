import os.path
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any

from decouple import config


def _to_bool(x: str) -> bool:
    if x.lower() == "false":
        return False
    return bool(x)


DEBUG: bool = config("BAD_DEBUG", default="false", cast=_to_bool)

# -- internal paths --

BASE_PATH: Path = config("BAD_BASE_PATH", default=Path(__file__).resolve().parent.parent, cast=Path)
SOURCE_PATH: Path = BASE_PATH / "bad"
STATIC_PATH: Path = SOURCE_PATH / "static"
TEMPLATE_PATH: Path = SOURCE_PATH / "templates"

# -- external paths --

DATA_PATH: Path = config("BAD_DATA_PATH", default=Path("~/").expanduser(), cast=Path)
TEMP_PATH: Path = config(
    "BAD_TEMP_PATH",
    default=str(Path(tempfile.gettempdir()) / "brainage-pipeline"),
    cast=Path,
)

MATLAB_PATH: Path = Path(config("BAD_MATLAB_PATH", default="", cast=str).rstrip("/"))
CAT12_PATH: Path = Path(config("BAD_CAT12_PATH", default="", cast=str).rstrip("/"))

# -- API server --

SERVER_HOST: str = config("BAD_SERVER_HOST", default="localhost", cast=str)
SERVER_PORT: int = config("BAD_SERVER_PORT", default=9009, cast=int)

# -- mongodb --

DATABASE_NAME: str = config("BAD_DATABASE_NAME", default="brainage-dev", cast=str)
DATABASE_HOST: str = config("BAD_DATABASE_HOST", default="localhost", cast=str)
DATABASE_PORT: int = config("BAD_DATABASE_PORT", default=27017, cast=int)
DATABASE_USER: Optional[str] = config("BAD_DATABASE_USER", default=None)
DATABASE_PASSWORD: Optional[str] = config("BAD_DATABASE_PASSWORD", default=None)


# -- utils --

def join_data_path(path: Union[str, Path]) -> Path:
    """
    Join `DATA_PATH` and `path`
    """
    path = str(path).lstrip(os.path.sep)
    return DATA_PATH / path


def relative_to_data_path(path: Union[str, Path]) -> Path:
    return Path(path).relative_to(DATA_PATH)


def to_dict(string_values: bool = False) -> dict:
    ret = {}
    for key, value in globals().items():
        if value is not None and key.isupper():
            if string_values:
                value = str(value)
            ret[key] = value
    return ret


class ConfigOverload:
    """
    Overloads/overwrites the configuration values.

    This does NOT work across different processes!

    Should ONLY be used by unittests, like so:

    ```python
    with config.ConfigOverload({
        "DATA_PATH": "/new/path",
    }):
        print(config.DATA_PATH)
    ```
    """
    def __init__(self, new_values: Dict[str, Any]):
        self.new_values = new_values
        self.old_values = {}

    def __enter__(self):
        for key, new_value in self.new_values.items():
            self.old_values[key] = old_value = globals().get(key)
            if old_value is not None:
                new_value = type(old_value)(new_value)
            globals()[key] = new_value

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key, old_value in self.old_values.items():
            globals()[key] = old_value
