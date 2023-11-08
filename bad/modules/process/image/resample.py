from typing import List, Generator

from bad.util.image import resample_to_shape
from ...base import ModuleGroup
from ...params import *
from .base import ImageProcessModuleBase, ImageObject


class ImageResampleModule(ImageProcessModuleBase):

    name = "image_resample"

    parameters = [
        ParameterSelect(
            name="mode",
            default_value="percent",
            options=[
                ParameterSelect.Option("percent", "percent"),
                ParameterSelect.Option("fixed", "fixed size"),
            ]
        ),
        ParameterFloat(
            name="output_percent",
            description="The output resolution in percent of the input",
            default_value=50,
            visible_js="mode === 'percent'",
        ),
        ParameterInt(
            name="output_x",
            description="The output resolution on x-axis",
            default_value=32,
            visible_js="mode === 'fixed'",
        ),
        ParameterInt(
            name="output_y",
            description="The output resolution on y-axis",
            default_value=32,
            visible_js="mode === 'fixed'",
        ),
        ParameterInt(
            name="output_z",
            description="The output resolution on z-axis",
            default_value=32,
            visible_js="mode === 'fixed'",
        ),
        ParameterSelect(
            name="interpolation",
            description="Type of interpolation for approximating voxel values",
            required=True,
            default_value="continuous",
            options=(
                ParameterSelect.Option("nearest", "none"),
                ParameterSelect.Option("linear", "linear"),
                ParameterSelect.Option("continuous", "continuous"),
            )
        ),
        *ImageProcessModuleBase.parameters
    ]

    def fixed_target_shape(self) -> Tuple[int, int, int]:
        return (
            self.get_parameter_value("output_x"),
            self.get_parameter_value("output_y"),
            self.get_parameter_value("output_z"),
        )

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:

        mode = self.get_parameter_value("mode")
        target_percent = self.get_parameter_value("output_percent")

        for image in images:
            if stub:
                src = image.src
            else:
                if mode == "fixed":
                    target_shape = self.fixed_target_shape()

                elif mode == "percent":
                    target_shape = tuple(
                        max(1, int(value * target_percent / 100))
                        for value in image.shape
                    )

                else:
                    raise ValueError(f"Invalid resample mode '{mode}'")

                src = resample_to_shape(
                    image.src,
                    shape=target_shape,
                    interpolation=self.get_parameter_value("interpolation"),
                )

            yield self.image_replace(
                image=image,
                src=src,
            )
