from typing import List, Generator

import nibabel
import nilearn.image
import numpy
import numpy as np

from bad import config
from ...base import ModuleGroup, ModuleTag
from ...params import *
from .base import ImageProcessModuleBase, ImageObject


class ImageSliceCombine(ImageProcessModuleBase):
    """
    Slices each input image and combines all slices.

    TODO: This is not suitable for the processing stage
    """
    name = "image_slice_combine"
    tags = [ModuleTag.MULTI_IMAGE_PROCESS]

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

        slices = []
        axis = self.get_parameter_value("slice_axis")
        dummy_image = None

        for image in images:
            if dummy_image and image.shape != dummy_image.shape:
                continue

            slice_args = [
                slice(None)
                for i in range(image.src.ndim)
            ]
            offset = min(self.get_parameter_value("slice_offset"), image.src.shape[axis] - 1)
            slice_args[axis] = slice(offset, offset + 1)

            slices.append(
                image.src.slicer[tuple(slice_args)].get_fdata()
            )
            if not dummy_image:
                dummy_image = image

        if slices:
            combined_array = numpy.concatenate(slices, axis=axis)
            combined_image = nibabel.Nifti1Image(
                combined_array,
                affine=dummy_image.src.affine,
            )
            yield self.image_replace(
                image=dummy_image,
                src=combined_image,
                filename="combined.nii.gz",
            )
