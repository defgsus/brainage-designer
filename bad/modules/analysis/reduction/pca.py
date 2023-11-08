import math
from pathlib import Path
from typing import Generator, List, Dict, Any

import numpy as np
from sklearn.decomposition import PCA

from bad import config
from bad.modules.base import Module, ModuleGroup, ModuleTag
from bad.modules.object import *
from bad.modules.params import *
from bad.modules.base import Module
from bad.util.image import nibabel_to_numpy_float
from bad.util.numpy_iterable import NumpyIterable
from .base import AnalysisReductionModuleBase


class AnalysisReductionPCA(AnalysisReductionModuleBase):

    name = "reduction_pca"
    combines_data = True

    parameters = [
        *AnalysisReductionModuleBase.parameters,
        ParameterInt(
            name="size",
            description="number of dimensions of feature vector",
            default_value=100,
        ),
    ]

    def reduce_images(
            self,
            images: NumpyIterable,
            model_params: dict
    ) -> np.ndarray:
        size = self.get_parameter_value("size")

        x = images.concat(flat=True)

        if not model_params.get("pca"):
            model_params["pca"] = PCA(
                n_components=size,
            )
            model_params["pca"].fit(x)

        return model_params["pca"].transform(x)

    def get_output_size(self, image: np.ndarray) -> int:
        return self.get_parameter_value("size")
