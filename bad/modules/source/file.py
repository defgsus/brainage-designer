from typing import Optional, Generator, Any

from ..base import Module, ModuleGroup, SourceModuleBase
from ..object.fileobject import FileObject


class FileSourceModuleBase(SourceModuleBase):
    group = [*SourceModuleBase.group, ModuleGroup.FILE]
    output_types = ["file"]

    def iter_objects(
            self,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
    ) -> Generator[FileObject, None, None]:
        raise NotImplementedError

