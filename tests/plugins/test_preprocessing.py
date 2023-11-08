import json
import os
from pathlib import Path
import tempfile
from tests.base import BadTestCase
from tests.testserver import TestServer

from bad import config

# register these plugins
import bad.plugins.essential
import bad.plugins.preprocess


class TestPreprocessing(BadTestCase):

    @BadTestCase.tag_server()
    def test_100_preprocessing(self):
        with config.ConfigOverload({
            "DATABASE_NAME": "bad-unittest",
            "DATA_PATH": self.DATA_PATH.parent,
        }):
            with tempfile.TemporaryDirectory(dir=config.DATA_PATH, prefix="bad-unittest-") as tmp_dir:
                tmp_dir = Path(tmp_dir)
                with TestServer() as server:
                    pipeline = server.create_pipeline(
                        target_path=config.relative_to_data_path(tmp_dir),
                    )
                    pipeline.add_module(
                        "image_source_directory",
                        {
                            "source_directory": "data/",
                            "glob_pattern": "avg152T1*",
                            "recursive": True,
                            "traverse_tar": True,
                        }
                    )
                    pipeline.add_module(
                        "image_source_directory",
                        {
                            "source_directory": "data/",
                            "glob_pattern": "minimal.nii*",
                            "recursive": True,
                        }
                    )
                    pipeline.add_module(
                        "image_resample",
                        {
                            "output_x": 42,
                        }
                    )

                    process_data = pipeline.run_process()
                    # print(json.dumps(process_data, indent=2))
                    objects = [
                        {
                            "sub_path": e["data"]["sub_path"],
                            "source_path": e["data"]["source_path"],
                            "loaded": e["data"]["actions"][0]["data"]["filename"],
                            "stored": e["data"]["actions"][-1]["data"]["filename"],
                        }
                        for e in process_data["events"]
                        if e["type"] == "object"
                    ]
                    # print(json.dumps(objects, indent=2))
                    self.assertIn(
                        {
                            "sub_path": ".",
                            "source_path": "data",
                            "loaded": "data/avg152T1_RL_nifti.nii.gz",
                            "stored": f"{tmp_dir.name}/image_resample/avg152T1_RL_nifti.nii.gz"
                        },
                        objects
                    )
                    self.assertIn(
                        {
                            "sub_path": ".",
                            "source_path": "data",
                            "loaded": "data/avg152T1_LR_nifti.nii.gz",
                            "stored": f"{tmp_dir.name}/image_resample/avg152T1_LR_nifti.nii.gz"
                        },
                        objects
                    )
                    self.assertIn(
                        {
                            "sub_path": "subdir",
                            "source_path": "data/subdir",
                            "loaded": "data/subdir/minimal.nii.gz",
                            "stored": f"{tmp_dir.name}/image_resample/subdir/minimal.nii.gz"
                        },
                        objects
                    )
                    self.assertIn(
                        {
                            "sub_path": "avg152T1_tar",
                            "source_path": "data",
                            "loaded": "data/avg152T1.tar/avg152T1_LR_nifti.nii.gz",
                            "stored": f"{tmp_dir.name}/image_resample/avg152T1_tar/avg152T1_LR_nifti.nii.gz"
                        },
                        objects
                    )
                    self.assertIn(
                        {
                            "sub_path": "avg152T1_tar",
                            "source_path": "data",
                            "loaded": "data/avg152T1.tar/avg152T1_RL_nifti.nii.gz",
                            "stored": f"{tmp_dir.name}/image_resample/avg152T1_tar/avg152T1_RL_nifti.nii.gz"
                        },
                        objects
                    )
