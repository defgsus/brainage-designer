import os.path
from pathlib import Path
from typing import Optional, Generator, IO, Union, List

from nibabel import all_image_classes


def strip_compression_extension(name: Union[str, Path]) -> Union[str, Path]:
    from bad.modules.object import FileObject

    is_path_class = isinstance(name, Path)
    name = str(name)
    name_lower = name.lower()
    for ext in FileObject.supported_compression_exts:
        if name_lower.endswith(ext):
            name = name[:-len(ext)]
            break

    return name if not is_path_class else Path(name)


def strip_extension(name: Union[str, Path]) -> Union[str, Path]:
    is_path_class = isinstance(name, Path)

    name = os.path.splitext(str(name))[0]

    return name if not is_path_class else Path(name)


def change_file_extension(filename: Union[str, Path], new_ext: str) -> Union[str, Path]:
    is_path_class = isinstance(filename, Path)
    result = Path(strip_compression_extension(filename)).with_suffix(new_ext)
    return result if is_path_class else str(result)


def add_file_extension(filename: Union[str, Path], *exts: str) -> Union[str, Path]:
    is_path_class = isinstance(filename, Path)
    result = ".".join((str(filename), *exts))
    return result if not is_path_class else Path(result)


def add_to_filename(
        filename: Union[str, Path],
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
) -> Union[str, Path]:
    is_path_class = isinstance(filename, Path)

    if isinstance(filename, str):
        filename = Path(filename)

    if prefix:
        filename = filename.parent / f"{prefix}{filename.name}"

    if suffix:
        new_name = filename.name.split(".")
        if not new_name:
            new_name = suffix
        else:
            new_name = ".".join((f"{new_name[0]}{suffix}", *new_name[1:]))
        filename = filename.parent / new_name

    return filename if is_path_class else str(filename)


def is_image_filename(filename: Union[str, Path]) -> bool:
    filename_lower = str(filename).lower()

    for image_klass in all_image_classes:
        for ext in image_klass.valid_exts:
            for suffix in ("", ) + image_klass._compressed_suffixes:
                ext = ext + suffix
                if filename_lower.endswith(ext):
                    return True

    return False
