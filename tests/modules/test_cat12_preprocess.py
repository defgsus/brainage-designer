import unittest
from pathlib import Path

import numpy as np

from bad import config
from bad.modules import *
from tests.base import BadTestCase


@unittest.skipIf(not config.CAT12_PATH.exists(), "CAT12 package not at it's place")
@unittest.skipIf(not config.MATLAB_PATH.exists(), "matlab not at it's place")
class TestCat12PreprocessModule(BadTestCase):

    @BadTestCase.tag_long()
    def test_cat12_preprocess(self):
        image = self.load_image_object("avg152T1_LR_nifti.nii.gz")

        module = ModuleFactory.new_module("cat12_preprocess", {
            "output_surface": 0,
            "output_bids": False,
            "gray_matter_native": False,
            "gray_matter_warped": False,
            "gray_matter_mod": 0,
            "gray_matter_dartel": 0,
            "affine_preprocessing": 0,
            "affine_regularisation": "none",
        })

        objects = list(module.process_objects([image]))
        for o in objects:
            print(o)
