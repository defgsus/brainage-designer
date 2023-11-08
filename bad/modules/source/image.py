from typing import Generator

from ..base import ModuleGroup, SourceModuleBase
from ..object.imageobject import ImageObject


class ImageSourceModuleBase(SourceModuleBase):
    group = [*SourceModuleBase.group, ModuleGroup.IMAGE]
    output_types = ["image"]

    def iter_objects(
            self,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
    ) -> Generator[ImageObject, None, None]:
        raise NotImplementedError
