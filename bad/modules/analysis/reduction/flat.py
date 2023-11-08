import math
from pathlib import Path
from typing import Generator, List, Dict, Any

import numpy as np

from bad import config
from bad.modules.base import Module, ModuleGroup, ModuleTag
from bad.modules.object import *
from bad.modules.params import *
from bad.modules.base import Module
from bad.util.image import nibabel_to_numpy_float
from bad.util.numpy_iterable import NumpyIterable
from .base import AnalysisReductionModuleBase


class AnalysisReductionFlat(AnalysisReductionModuleBase):

    name = "reduction_flat"

    parameters = [
        *AnalysisReductionModuleBase.parameters,
        ParameterBool(
            name="fixed_size",
            description="Set a fixed number of dimensions",
            default_value=False,
        ),
        ParameterInt(
            name="size",
            description="number of dimensions of feature vector",
            default_value=100,
            visible_js="fixed_size === true",
        ),
    ]

    def reduce_images(
            self,
            images: NumpyIterable,
            model_params: dict,
    ) -> np.ndarray:
        fixed_size = self.get_parameter_value("fixed_size")
        size = self.get_parameter_value("size")

        array_list = []
        for image in images:
            flat = image.reshape(1, -1)
            if fixed_size:
                flat = flat[:size]
            array_list.append(flat)

        return np.concatenate(array_list)

    def get_output_size(self, image: np.ndarray) -> int:
        if self.get_parameter_value("fixed_size"):
            return self.get_parameter_value("size")
        return math.prod(image.shape)
