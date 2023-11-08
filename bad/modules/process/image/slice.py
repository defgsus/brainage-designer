from typing import List, Generator

import nibabel
import nilearn.image
import numpy
import numpy as np

from bad import config
from ...base import ModuleGroup, ModuleTag
from ...params import *
from .base import ImageProcessModuleBase, ImageObject


class ImageSlice(ImageProcessModuleBase):
    name = "image_slice"
    help = """
    Slice a 2-dimensional array from 3-dimensional voxels. 
    """

    parameters = [
        ParameterInt(
            name="slice_axis",
            description="Select axis of slice",
            min_value=0,
        ),
        ParameterInt(
            name="slice_offset",
            description="Voxel offset of the slice",
            min_value=0,
        ),
        *ImageProcessModuleBase.parameters
    ]

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:
        if stub:
            yield from images

        axis = self.get_parameter_value("slice_axis")
        slice_offset = self.get_parameter_value("slice_offset")

        for image in images:

            slice_args = [
                slice(None)
                for i in range(image.src.ndim)
            ]
            offset = min(slice_offset, image.src.shape[axis] - 1)
            slice_args[axis] = slice(offset, offset + 1)

            yield self.image_replace(
                image,
                src=image.src.slicer[tuple(slice_args)]
            )
