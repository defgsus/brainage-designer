from typing import Generator

from ..base import SourceModuleBase, ModuleGroup
from ..object import ImageObject
from ..source import FileSourceDirectoryModule


class ImageSourceDirectoryModule(FileSourceDirectoryModule):

    name = "image_source_directory"
    group = [*SourceModuleBase.group, ModuleGroup.IMAGE]
    output_types = [ImageObject.data_type]

    def iter_objects(
            self,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
    ) -> Generator[ImageObject, None, None]:
        for obj in super().iter_objects(interval=interval, offset=offset):
            img = obj.read_nibabel()
            if img:
                yield img
