import json
import os
from pathlib import Path
import tempfile
from tests.base import BadTestCase
from tests.testserver import TestServer

from bad import config

# register these plugins
import bad.plugins.essential


class TestFilesPlugin(BadTestCase):

    @BadTestCase.tag_server()
    def test_100_preprocessing(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH.parent,
        }):
            with TestServer() as server:
                response = server.GET(
                    "api/files/image/meta/",
                    {"path": "data/avg152T1_LR_nifti.nii.gz"},
                )
                self.assertEqual(
                    {
                        'path': 'data/avg152T1_LR_nifti.nii.gz',
                        'shape': [91, 109, 91],
                        'dtype': 'uint8',
                        'voxel_size': [2, 2, 2],
                    },
                    response.json(),
                )

                # -- read within tar file :thumbsup: --

                response = server.GET(
                    "api/files/image/meta/",
                    {"path": "data/avg152T1.tar/avg152T1_LR_nifti.nii.gz"},
                )
                self.assertEqual(
                    {
                        'path': 'data/avg152T1.tar/avg152T1_LR_nifti.nii.gz',
                        'shape': [91, 109, 91],
                        'dtype': 'uint8',
                        'voxel_size': [2, 2, 2],
                    },
                    response.json(),
                )
