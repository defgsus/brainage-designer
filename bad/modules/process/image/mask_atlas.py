import math
from typing import List, Generator

import nibabel
import nilearn.image
import numpy
import numpy as np

from bad import config
from ...base import ModuleGroup, ModuleTag
from ...params import *
from .base import ImageProcessModuleBase, ImageObject
from bad.util.image import to_output_dtype


class ImageMaskAtlasModule(ImageProcessModuleBase):

    name = "image_mask_atlas"
    tags = [ModuleTag.MULTI_IMAGE_PROCESS]

    help = """
    Split the input image into several output images, each representing one region
    defined by an *atlas* image. 
    
    The atlas file must be in **integer format**, each number representing 
    one region.
    
    Each region will be added to the filename, e.g.

        dir/brain.nii
        
    will be split into
    
        dir/mask_1/brain.nii
        dir/mask_2/brain.nii
        ...
    
    The resulting images can be automatically cropped to the minimum shape required to
    represent each region.   
    """

    parameters = [
        ParameterFilename(
            name="atlas_file",
            description="The filename of the atlas",
        ),
        ParameterSelect(
            name="interpolation",
            description="Type of interpolation used for resampling to the atlas shape",
            default_value="continuous",
            options=(
                ParameterSelect.Option("nearest", "none"),
                ParameterSelect.Option("linear", "linear"),
                ParameterSelect.Option("continuous", "continuous"),
            ),
            help="""
            If the shape of the input image does not match the shape of the atlas, it
            will be resampled to the atlas shape.
            
            The **continuous** setting usually creates the best results. 
            """,
        ),
        ParameterBool(
            name="crop_result", default_value=True,
            description="Crop the resulting images to the region of interest",
        ),
        ParameterInt(
            name="max_num_voxels", default_value=0, min_value=0,
            description="If not zero, skip all regions that produce more voxels than this number",
        ),
        ParameterSelect(
            name="output_dtype", default_value="float32",
            options=[
                ParameterSelect.Option("uint8", "8 bit unsigned int"),
                ParameterSelect.Option("float32", "32 bit float"),
                ParameterSelect.Option("float64", "64 bit float"),
            ],
            description="date type of output",
        ),
        *ImageProcessModuleBase.parameters
    ]

    def prepare(self):
        self.atlas = nibabel.load(
            config.join_data_path(self.get_parameter_value("atlas_file"))
        )
        self.atlas_array = self.atlas.dataobj.get_unscaled()
        atlas_mask_values = sorted(np.unique(self.atlas_array))
        self.atlas_mask_values = []

        do_crop = self.get_parameter_value("crop_result")
        max_voxels = self.get_parameter_value("max_num_voxels")

        # prepare the slices for cropping the image
        self.crop_slices = {}
        if not (do_crop or max_voxels):
            self.atlas_mask_values = atlas_mask_values
        else:
            for mask_value in atlas_mask_values:
                mask_array = (self.atlas_array == mask_value).astype("uint8")
                mask = nibabel.Nifti1Image(mask_array, affine=self.atlas.affine)
                mask, crop_slices = nilearn.image.crop_img(
                    mask, pad=True, return_offset=True,
                )
                if max_voxels and math.prod(mask.shape) > max_voxels:
                    continue

                self.atlas_mask_values.append(mask_value)

                if do_crop:
                    self.crop_slices[mask_value] = crop_slices

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:

        output_dtype = self.get_parameter_value("output_dtype")

        for image in images:

            if stub or self.atlas.shape == image.shape:
                brain = image.src
            else:
                brain = nilearn.image.resample_to_img(
                    source_img=image.src,
                    target_img=self.atlas,
                    interpolation=self.get_parameter_value("interpolation")
                )

            for mask_value in self.atlas_mask_values:
                if stub:
                    masked_image = image
                else:
                    mask = (self.atlas_array == mask_value)#.astype("uint8")

                    masked_data = brain.dataobj * mask

                    # TODO: this has to be tested for all possible dtypes
                    #   and put into every module (with some overriding options)
                    #if masked_data.dtype != image.dtype:
                    #    masked_data = (masked_data / image.src.dataobj.slope).astype(image.dtype)

                    masked_data = to_output_dtype(masked_data, output_dtype)

                    #print(masked_data.dtype, masked_data.min(), masked_data.max())

                    masked_image = nibabel.Nifti1Image(
                        masked_data,
                        affine=brain.affine,
                    )

                    if mask_value in self.crop_slices:
                        masked_image = masked_image.slicer[self.crop_slices[mask_value]]

                yield self.image_replace(
                    image=image,
                    action_name=f"mask_{mask_value}",
                    src=masked_image,
                    add_sub_path=f"mask_{mask_value}",
                )
