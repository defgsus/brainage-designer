from .base import *


class Cat12Smooth(Cat12ModuleBase):
    name = "cat12_smooth"

    parameters = [
        ParameterFloat(
            name="smooth_x", default_value=6., min_value=0.01,
        ),
        ParameterFloat(
            name="smooth_y", default_value=6., min_value=0.01,
        ),
        ParameterFloat(
            name="smooth_z", default_value=6., min_value=0.01,
        ),
        *Cat12ModuleBase.parameters
    ]

    def process_nii_files(
            self,
            input_images: Iterable[ImageObject],
            image_filenames: Iterable[Path],
            stub: bool = False,
    ) -> Generator[Union[ImageObject, FileObject], None, None]:
        if not stub:
            self.call_cat12(
                "cat_standalone_smooth",
                "-a1", repr(self.smooth_vector()),
                "-a2", " 'smooth_' ",
                *image_filenames,
            )
        for image, new_filename in zip(input_images, image_filenames):
            if stub:
                yield self.image_replace(image)
            else:
                yield self.image_replace(
                    image,
                    src=new_filename.parent / f"smooth_{new_filename.name}",
                )

    def smooth_vector(self) -> List[float]:
        return [
            self.get_parameter_value("smooth_x"),
            self.get_parameter_value("smooth_y"),
            self.get_parameter_value("smooth_z"),
        ]
