import tempfile
from pathlib import Path
import unittest
import json
from typing import Iterable, Generator, Optional, Union

import numpy as np

from bad import config
from bad.modules import *
from bad.plugins.analysis import Analysis, AnalysisReduction
from tests.base import BadTestCase


class TestAnalysis(BadTestCase):

    def run_analysis_ixi(
            self,
            extra_modules: Iterable[Module],
            analysis_model: AnalysisModelBase,
            target_attribute: str = "age",
            ixi_path: Optional[Union[str, Path]] = None,
            num_files: int = 8,
            num_valid_files: int = 8,
            num_validation: int = 2,
            num_repeat: int = 10,
    ):
        if ixi_path:
            ixi_path = Path(ixi_path)
        else:
            ixi_path = self.DATA_PATH.relative_to(config.DATA_PATH) / "ixi32"

        table_file = self.DATA_PATH.relative_to(config.DATA_PATH) / "ixi32" / "IXI.xls"

        reduction = AnalysisReduction(
            modules=[
                ModuleFactory.new_module("analysis_source", {
                    "source_directory": str(ixi_path),
                    "glob_pattern": "*.nii*",
                    "filename_regex": "[^\d]*(?P<id>\d+)",
                    "table_file": str(table_file),
                    "table_mapping": {"IXI_ID": "id", "AGE": "age"},
                }, prepare=True),
                *extra_modules,
            ],
            separation_values={
                "separation": "cross_validation",
                "split_number": num_validation,
                "split_number_type": "absolute",
                "num_repeat": num_repeat,
            },
        )
        reduction.init()

        self.assertEqual(num_files, len(reduction.files))
        files1, files2 = reduction.split_files_to_train_and_validation()
        self.assertEqual(num_valid_files - num_validation, len(files1))
        self.assertEqual(num_validation, len(files2))

        with tempfile.TemporaryDirectory(
                dir=self.DATA_PATH, prefix="bad-unittest-reduction-"
        ) as target_path:
            target_path = Path(target_path)

            analysis = Analysis(
                reduction=reduction,
                analysis_model=analysis_model,
                form_values={
                    "target_path": config.relative_to_data_path(target_path),
                    "target_attribute": target_attribute,
                }
            )

            analysis.train()

            report = analysis.report()
            print(json.dumps(report, indent=2))

            for run in report["runs"]:
                self.assertGreater(run["predicted_value_std"], 0.001)

            # assert mean absolute error <= 20 years
            self.assertLessEqual(report["average"]["validation_loss_l1"], 20)
            self.assertLessEqual(report["average"]["validation_loss_l2"], 300)

    def test_100_flat_rvr(self):
        self.run_analysis_ixi(
            extra_modules=[
                ModuleFactory.new_module("reduction_flat", prepare=True),
            ],
            analysis_model=ModuleFactory.new_module("analysis_rvr"),
        )

    def test_110_pca_rvr(self):
        self.run_analysis_ixi(
            extra_modules=[
                ModuleFactory.new_module("reduction_pca", {"size": 6}, prepare=True),
            ],
            analysis_model=ModuleFactory.new_module("analysis_rvr"),
        )

    @unittest.skipIf(
        not config.join_data_path("prog/data/TEST/ixi32/image_resample/IXI-T1_tar").exists(),
        "No ixi dataset found"
    )
    def test_120_slice_pca_rvr_full_ixi(self):
        self.run_analysis_ixi(
            extra_modules=[
                ModuleFactory.new_module("image_slice", {"slice_axis": 1, "slice_offset": 16}, prepare=True),
                ModuleFactory.new_module("reduction_pca", {"size": 100}, prepare=True),
            ],
            analysis_model=ModuleFactory.new_module("analysis_rvr"),
            ixi_path = Path("prog/data/TEST/ixi32/image_resample/IXI-T1_tar"),
            num_files=581,
            num_valid_files=563,
            num_validation=20,
            num_repeat=3,
        )
