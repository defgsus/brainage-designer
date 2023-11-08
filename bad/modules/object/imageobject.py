from pathlib import Path
from typing import Optional, Generator, Tuple, Union, List

import nibabel
import numpy as np
from nibabel.filebasedimages import SerializableImage
from nibabel import all_image_classes

from bad import logger
from bad.util.filenames import add_to_filename
from .base import ModuleObject, ModuleObjectType


SUPPORTED_IMAGE_EXTENSIONS = set()
for klass in all_image_classes:
    for ext in klass.valid_exts:
        for suffix in ("", ".gz", ".bz2"):
            SUPPORTED_IMAGE_EXTENSIONS.add(f"{ext}{suffix}")


def filename_matches_supported_image_formats(filename: Union[str, Path]) -> bool:
    parts = str(filename).lower().split(".")
    if not parts:
        return False

    ext = parts[-1]
    if ext in ("gz", "bz2") and len(parts) > 1:
        ext = parts[-2]

    return f".{ext}" in SUPPORTED_IMAGE_EXTENSIONS


class ImageObject(ModuleObject):
    data_type = ModuleObjectType.IMAGE

    STUB_IMAGE = nibabel.Nifti1Image(
        dataobj=np.ndarray((8, 8, 8), dtype=np.int8),
        affine=np.diag((1, 1, 1, 0)),
    )

    def __init__(
            self,
            src: SerializableImage,
            filename: str,
            sub_path: Union[str, Path],
            source_path: Union[str, Path],
            actions: Optional[List[dict]] = None,
            source: Optional[dict] = None,
    ):
        super().__init__(actions=actions, source=source)
        self.src = src
        self.filename: str = str(filename)
        self.sub_path: Path = Path(str(sub_path).rstrip("/"))
        self.source_path: Path = Path(str(source_path).rstrip("/"))

    def __repr__(self):
        return f"Image({self.shape}, '{self.sub_path}', '{self.filename}')"

    def discard(self):
        src = self.src
        self.src = None
        del src

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "filename": self.filename,
            "sub_path": str(self.sub_path),
            "source_path": str(self.source_path),
        }

    def replace(
            self,
            action: dict,
            src: Optional[Union[SerializableImage, str, Path]] = None,
            filename: Optional[str] = None,
            filename_prefix: Optional[str] = None,
            filename_suffix: Optional[str] = None,
            sub_path: Optional[Union[str, Path]] = None,
            add_sub_path: Optional[Union[str, Path]] = None,
    ) -> "ImageObject":
        """
        Replace the image (or just the filename) and store an action.

        :param src: nibabel image or a filename
            Attention! If passing a `nibabel.load()` image which is not `in_memory` and
            the file is removed afterwards (because it's in a temporary directory)
            the image will not be usable! Pass the filename instead to
            automatically create an `in_memory` image

        :param action: a dict with at least a `name` property
        :return: new ImageObject instance
        """
        if src is not None:
            if isinstance(src, (str, Path)):
                image = nibabel.load(src)
                src = nibabel.Nifti1Image(
                    image.dataobj.__array__(),
                    affine=image.affine,
                    header=image.header,
                )

        filename = str(self.filename if filename is None else filename)
        filename = add_to_filename(filename, filename_prefix, filename_suffix)

        new_sub_path = self.sub_path if sub_path is None else sub_path
        if add_sub_path:
            new_sub_path = Path(new_sub_path) / add_sub_path

        new_image = self.__class__(
            src=self.src if src is None else src,
            filename=filename,
            sub_path=new_sub_path,
            source_path=self.source_path,
            actions=self.actions + [action]
        )
        new_image.source = self.source or self.to_dict()
        return new_image

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.src.header.get_data_shape()

    @property
    def dtype(self) -> Tuple[np.dtype, ...]:
        return self.src.header.get_data_dtype()

    @property
    def voxel_size(self) -> Tuple[float, ...]:
        return tuple(float(i) for i in self.src.header.get_zooms())
