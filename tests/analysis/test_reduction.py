import tempfile
from pathlib import Path
import unittest
import json
from typing import Iterable, Generator

import numpy as np

from bad import config
from bad.modules import *
from bad.plugins.analysis.reduction import AnalysisReduction
from tests.base import BadTestCase



class TestReduction(BadTestCase):

    def test_100_parameters(self):
        self.assertIsNone(
            ModuleFactory.new_module("reduction_flat").get_parameter_value("reduce_sets_separately")
        )
        self.assertIsNotNone(
            ModuleFactory.new_module("reduction_pca").get_parameter_value("reduce_sets_separately")
        )

    def test_200_a_couple_of_reductions(self):
        ixi_path = self.DATA_PATH.relative_to(config.DATA_PATH) / "ixi32"

        for reduction_module, reduction_params, expected_feature_size in (
                ("reduction_flat", {"fixed_size": False}, 32 ** 3),
                ("reduction_pca", {"size": 4}, 4),
        ):
            reduction = AnalysisReduction(
                modules=[
                    ModuleFactory.new_module("analysis_source", {
                        "source_directory": str(ixi_path),
                        "glob_pattern": "*.nii*",
                        "filename_regex": "[^\d]*(?P<id>\d+)",
                        "table_file": str(ixi_path / "IXI.xls"),
                        "table_mapping": {"IXI_ID": "id", "AGE": "age"},
                    }),
                    ModuleFactory.new_module(reduction_module, reduction_params),
                ],
                separation_values={
                    "separation": "cross_validation",
                    "split_number": 2,
                    "split_number_type": "absolute",
                },
            )
            reduction.init()

            self.assertEqual(8, len(reduction.files))
            files1, files2 = reduction.split_files_to_train_and_validation()
            self.assertEqual(6, len(files1))
            self.assertEqual(2, len(files2))

            with tempfile.TemporaryDirectory(prefix="bad-unittest-reduction") as target_path:
                target_path = Path(target_path)

                reduction.run_reduction(target_path)

                train_features, train_attributes, \
                    validation_features, validation_attributes = reduction.load_reduction(target_path)

                self.assertEqual((6, expected_feature_size), train_features.shape)
                self.assertEqual((2, expected_feature_size), validation_features.shape)

                self.assertEqual((6, 2), train_attributes.shape)
                self.assertEqual((2, 2), validation_attributes.shape)
                #print(train_attributes)
                #print(validation_attributes)
