from typing import List, Generator

from bad.util.image import resample_to_shape
from ...base import ModuleGroup
from ...params import *
from .base import ImageProcessModuleBase, ImageObject


class ImageNoopModule(ImageProcessModuleBase):

    name = "image_noop"
    help = "Just for debugging. Module does nothing."

    parameters = [
        *ImageProcessModuleBase.parameters
    ]

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:
        for image in images:
            yield image
