import os
import json
import unittest
from pathlib import Path

import numpy as np

from bad import config
from bad.modules import *
from tests.base import BadTestCase


class TestSliceModule(BadTestCase):

    def test_100_slice_xyz(self):
        image = self.load_image_object("avg152T1_LR_nifti.nii.gz")
        self.assertEqual((91, 109, 91), image.shape)

        for expected_shape, module_params in (
                ((1, 109, 91), {"slice_axis": 0}),
                ((91, 1, 91), {"slice_axis": 1}),
                ((91, 109, 1), {"slice_axis": 2}),
        ):
            module = ModuleFactory.new_module("image_slice", module_params)

            output_image = list(module.process_objects([image]))[0]

            self.assertEqual(expected_shape, output_image.shape)

