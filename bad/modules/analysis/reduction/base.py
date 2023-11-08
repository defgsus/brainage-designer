import glob
import re
from pathlib import Path
from typing import Generator, List, Dict, Any

import numpy as np

from bad import config
from bad.util.filenames import is_image_filename
from bad.util.table import read_table
from bad.modules.base import Module, ModuleGroup, ModuleTag
from bad.modules.object import *
from bad.modules.params import *
from bad.modules.base import Module
from bad.util.numpy_iterable import NumpyIterable


class AnalysisReductionModuleBase(Module):

    tags = [ModuleTag.ANALYSIS]
    output_types = []
    group = [ModuleGroup.REDUCTION, ModuleGroup.IMAGE]
    combines_data: bool = False

    parameters = [
    ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.combines_data:
            cls.parameters = [
                ParameterBool(
                    name="reduce_sets_separately",
                    description="reduce training and validation sets individually",
                    default_value=False,
                ),
            ] + cls.parameters

    def reduce_images(
            self,
            images: NumpyIterable,
            model_params: dict,
    ) -> np.ndarray:
        raise NotImplementedError

    def get_output_size(self, image: np.ndarray) -> int:
        raise NotImplementedError
