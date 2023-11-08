from .base import *


class Cat12Deface(Cat12ModuleBase):
    name = "cat12_deface"

    def process_nii_files(
            self,
            input_images: Iterable[ImageObject],
            image_filenames: Iterable[Path],
            stub: bool = False,
    ) -> Generator[Union[ImageObject, FileObject], None, None]:
        if not stub:
            self.call_cat12(
                "cat_standalone_deface",
                *image_filenames,
            )
        for image, new_filename in zip(input_images, image_filenames):
            if stub:
                yield self.image_replace(image)
            else:
                yield self.image_replace(
                    image,
                    src=new_filename.parent / f"anon_{new_filename.name}",
                )

