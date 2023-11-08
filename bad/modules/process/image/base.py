from pathlib import Path
from typing import Generator, Iterable, Optional, Union

from nibabel.filebasedimages import SerializableImage

from ...base import ProcessModuleBase, ModuleGroup, ModuleTag
from ...object.base import ModuleObjectType
from ...object.imageobject import ImageObject


class ImageProcessModuleBase(ProcessModuleBase):
    tags = [ModuleTag.IMAGE_PROCESS]
    group = [*ProcessModuleBase.group, ModuleGroup.IMAGE]
    input_types = [ModuleObjectType.IMAGE]
    output_types = [ModuleObjectType.IMAGE]

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False,
    ) -> Generator[ImageObject, None, None]:
        raise NotImplementedError

    def image_replace(
            self,
            image: ImageObject,
            action_name: Optional[str] = None,
            src: Optional[Union[SerializableImage, str, Path]] = None,
            filename: Optional[Union[str, Path]] = None,
            filename_prefix: Optional[str] = None,
            filename_suffix: Optional[str] = None,
            sub_path: Optional[Union[str, Path]] = None,
            add_sub_path: Optional[Union[str, Path]] = None,
    ) -> ImageObject:
        """
        Use this method instead of `ImageObject.replace`!
        It will add the correct action dictionary
        """
        action_dict = self.action_dict(action_name=action_name)
        return image.replace(
            action=action_dict,
            src=src,
            filename=filename,
            filename_prefix=filename_prefix,
            filename_suffix=filename_suffix,
            sub_path=sub_path,
            add_sub_path=add_sub_path,
        )
