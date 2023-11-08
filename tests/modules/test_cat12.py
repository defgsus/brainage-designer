import os
import json
import unittest
from pathlib import Path

import numpy as np

from bad import config
from bad.modules import *
from tests.base import BadTestCase


@unittest.skipIf(not config.CAT12_PATH.exists(), "CAT12 package not at it's place")
@unittest.skipIf(not config.MATLAB_PATH.exists(), "matlab not at it's place")
class TestCat12Modules(BadTestCase):

    def test_cat12_version(self):
        module = ModuleFactory.new_module("cat12_smooth")
        version = module.cat12_version()
        self.assertTrue(version.startswith("12."), f"Got '{version}'")

    @BadTestCase.tag_long()
    def test_cat12_smooth(self):
        image = self.load_image_object("avg152T1_LR_nifti.nii.gz")

        module = ModuleFactory.new_module("cat12_smooth")
        output_image = next(module.process_objects([image]))
        print(json.dumps(output_image.to_dict(), indent=2))

        self.assertEqual(image.sub_path, output_image.sub_path)
        self.assertEqual(image.filename, output_image.filename)
        self.assertEqual("cat12_smooth", output_image.actions[0]["name"])

    @BadTestCase.tag_long()
    def test_cat12_deface(self):
        image = self.load_image_object("avg152T1_LR_nifti.nii.gz")

        module = ModuleFactory.new_module("cat12_deface")
        output_image = list(module.process_objects([image]))[0]

        self.assertEqual(image.sub_path, output_image.sub_path)
        self.assertEqual(image.filename, output_image.filename)
        self.assertEqual("cat12_deface", output_image.actions[0]["name"])

        self.assertLess(
            np.sum(output_image.src.get_fdata().flatten()),
            np.sum(image.src.get_fdata().flatten()),
            "Output image should have 'less data' than input image"
        )
