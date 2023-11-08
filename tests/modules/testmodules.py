from pathlib import Path
from typing import Iterable, Generator, Union

import nibabel.processing
import numpy as np

from bad import config
from bad.util.filenames import change_file_extension
from bad.modules import *
from tests.base import BadTestCase


class MultiImageModule(ImageProcessModuleBase):
    """
    Just a simple image process that creates two outputs for every input
    """
    name = "test_multi_image"

    parameters = [
        *ImageProcessModuleBase.parameters,
        ParameterInt(
            name="smooth_1", default_value=10,
        ),
        ParameterInt(
            name="smooth_2", default_value=20,
        )
    ]

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:
        for image in images:
            smooth_1 = self.get_parameter_value("smooth_1")
            smooth_2 = self.get_parameter_value("smooth_2")

            kwargs = {
                "action_name": f"smooth_1",
                "filename_prefix": f"sm{smooth_1}_",
            }
            if not stub:
                kwargs["src"] = nibabel.processing.smooth_image(image.src, smooth_1)

            yield self.image_replace(image, **kwargs)

            kwargs = {
                "action_name": f"smooth_2",
                "filename_suffix": f"_sm{smooth_2}",
            }
            if not stub:
                kwargs["src"] = nibabel.processing.smooth_image(image.src, smooth_2)

            yield self.image_replace(image, **kwargs)


class ImageAndFileModule(ImageProcessModuleBase):
    """
    Creates an image object ("prefix_<filename>")
    and a file object ("<filename>.txt")
    """
    name = "test_image_and_file"
    output_types = [ModuleObjectType.IMAGE, ModuleObjectType.FILE]

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False,
    ) -> Generator[Union[ImageObject, FileObject], None, None]:
        for image in images:

            yield self.image_replace(
                image,
                action_name="just add prefix",
                filename_prefix="prefix_",
            )
            yield FileObjectMemory(
                content=f"A text file from {image.filename}",
                filename=change_file_extension(image.filename, ".txt"),
                sub_path=image.sub_path,
                source_path=image.source_path,
                actions=image.actions,
                source=image.source,
            )
