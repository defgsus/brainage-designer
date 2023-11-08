import unittest
import json
from typing import Iterable, Generator

from bad import config
from bad.modules import *
from tests.base import BadTestCase
# register test modules
from tests.modules import testmodules


class TestSourceFiles(BadTestCase):

    def test_100_file_attributes(self):
        module: AnalysisSourceModule = ModuleFactory.new_module(
            name=AnalysisSourceModule.name,
            parameters={
                "source_directory": str(self.DATA_PATH.relative_to(config.DATA_PATH) / "ixi32"),
                "glob_pattern": "*.nii*",
                #"filename_regex": "[^\d]*(?P<id>\d+)",
                "filename_regex": "IXI(?P<id>\d+)-[^\d]+-(?P<id2>\d+)",
            },
        )

        filenames = sorted(
            (
                (str(i[0]), i[1])
                for i in module.iter_filenames(require_id=False)
            ),
            key=lambda i: i[0]
        )
        self.assertEqual(
            [
                ('IXI002-Guys-0828-T1.nii.gz', {"id": "002", "id2": "0828"}),
                ('IXI012-HH-1211-T1.nii.gz', {"id": "012", "id2": "1211"}),
                ('IXI013-HH-1212-T1.nii.gz', {"id": "013", "id2": "1212"}),
                ('IXI014-HH-1236-T1.nii.gz', {"id": "014", "id2": "1236"}),
                ('IXI015-HH-1258-T1.nii.gz', {"id": "015", "id2": "1258"}),
                ('IXI016-Guys-0697-T1.nii.gz', {"id": "016", "id2": "0697"}),
                ('IXI017-Guys-0698-T1.nii.gz', {"id": "017", "id2": "0698"}),
                ('IXI019-Guys-0702-T1.nii.gz', {"id": "019", "id2": "0702"}),
            ],
            filenames
        )

    def test_200_table_attributes(self):
        ixi_path = self.DATA_PATH.relative_to(config.DATA_PATH) / "ixi32"
        module: AnalysisSourceModule = ModuleFactory.new_module(
            name=AnalysisSourceModule.name,
            parameters={
                "source_directory": str(ixi_path),
                "glob_pattern": "*.nii*",
                "filename_regex": "[^\d]*(?P<id>\d+)",
                "table_file": str(ixi_path / "IXI.xls"),
                "table_mapping": {"IXI_ID": "id", "AGE": "age"},
            },
        )

        filenames = sorted(
            (
                (str(i[0]), i[1])
                for i in module.iter_filenames_with_table_attributes(require_id=False)
            ),
            key=lambda i: i[0]
        )

        self.assertEqual(
            [
                ('IXI002-Guys-0828-T1.nii.gz', {"id": "002", "age": 35.800136892539356, "_status": "ok"}),
                ('IXI012-HH-1211-T1.nii.gz', {"id": "012", "age": 38.78165639972622, "_status": "ok"}),
                ('IXI013-HH-1212-T1.nii.gz', {"id": "013", "age": 46.71047227926078, "_status": "ok"}),
                ('IXI014-HH-1236-T1.nii.gz', {"id": "014", "age": 34.23682409308692, "_status": "ok"}),
                ('IXI015-HH-1258-T1.nii.gz', {"id": "015", "age": 24.28473648186174, "_status": "ok"}),
                ('IXI016-Guys-0697-T1.nii.gz', {"id": "016", "age": 55.167693360711844, "_status": "ok"}),
                ('IXI017-Guys-0698-T1.nii.gz', {"id": "017", "age": 29.09240246406571, "_status": "ok"}),
                ('IXI019-Guys-0702-T1.nii.gz', {"id": "019", "age": 58.65845311430527, "_status": "ok"}),
            ],
            filenames
        )
