import os
import time
import glob
import shutil
import tempfile
import unittest
import json
from pathlib import Path
from typing import Iterable, Generator, Optional, Union

import numpy as np

from bad import config
from bad.modules import *
from tests.base import BadTestCase
from tests.test_fileobject import FILENAME_IXI_T1
# register modules
from tests.modules import testmodules


class TestModuleGraphSkip(BadTestCase):

    def create_source_module(
            self,
            type: str = "file",
            source_directory: Optional[Union[str, Path]] = None,
            glob_pattern: str = "avg152T1*",
            sub_path: Optional[str] = None,
            traverse_tar: bool = True,
            recursive: bool = False,
    ):
        """
        This creates a "<type>_source_directory" module
        which yields 4 files by default
            (the avg152T1_LR/RL.. files and the same from the tar file)
        """
        if not source_directory:
            source_directory = str(self.DATA_PATH.relative_to(config.DATA_PATH))

        return ModuleFactory.new_module(
            f"{type}_source_directory",
            {
                "source_directory": str(source_directory),
                "glob_pattern": glob_pattern,
                "recursive": recursive,
                "traverse_tar": traverse_tar,
                "module_object_sub_path": sub_path or "",
            }
        )

    @unittest.skipIf(not FILENAME_IXI_T1.exists(), f"missing file {FILENAME_IXI_T1}")
    def test_100_stub_runs_fast(self):
        with config.ConfigOverload({
            "DATA_PATH": "/",
        }):
            with tempfile.TemporaryDirectory(prefix="bad-tests-") as tmp_dir:
                tmp_dir = Path(tmp_dir)

                graph = ModuleGraph(
                    [
                        ModuleFactory.new_module(
                            "dataset_ixi",
                            {
                                "local_path": FILENAME_IXI_T1.parent
                            }
                        ),
                        ModuleFactory.new_module("cat12_preprocess")
                    ],
                    target_path=config.relative_to_data_path(tmp_dir),
                )

                start_time = time.time()
                stub_objects = list(graph.iter_graph_objects(stub=True))
                run_time = time.time() - start_time

                # should run in less than 2 seconds
                self.assertLessEqual(run_time, 2.)
                # should contain 580 ixi-images x 5 cat12-preprocessing versions
                self.assertGreaterEqual(len(stub_objects), 580 * 5)

    def test_200_skip_existing_or_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="bad-tests-") as tmp_dir:
            tmp_dir = Path(tmp_dir)
            os.makedirs(tmp_dir / "source")
            os.makedirs(tmp_dir / "target")

            # copy a few files
            shutil.copy(self.DATA_PATH / "avg152T1_LR_nifti.nii.gz", tmp_dir / "source")
            shutil.copy(self.DATA_PATH / "avg152T1_RL_nifti.nii.gz", tmp_dir / "source")
            shutil.copy(self.DATA_PATH / "avg152T1.tar", tmp_dir / "source")

            with config.ConfigOverload({
                "DATA_PATH": tmp_dir,
            }):

                graph = ModuleGraph(
                    [
                        ModuleFactory.new_module("image_source_directory", {
                            "source_directory": "source",
                            "glob_pattern": "*",
                            "traverse_tar": True,
                        }),
                        ModuleFactory.new_module("test_image_and_file"),
                        ModuleFactory.new_module("image_resample", {"module_result_path": "final"}),
                    ],
                    target_path="target",
                    # first test skip-if-file-exists mode
                    skip_policy=ModuleGraph.SkipPolicy.EXISTS,
                )

                # run stub mode
                stub_objects = list(graph.iter_graph_objects(stub=True))
                self.assertEqual(4, graph.report["source_objects"])
                self.assertEqual(8, graph.report["target_objects"])
                self.assertEqual(0, graph.report["skipped_objects"])
                self.assertEqual(8, len(stub_objects))

                # no files yet
                self.assertEqual(
                    [],
                    sorted(
                        p[len(str(tmp_dir / "target")):]
                        for p in glob.glob(str(tmp_dir / "target" / "**" / "*"), recursive=True)
                    )
                )

                graph.clear_report()
                true_objects = list(graph.iter_graph_objects(stub=False))
                self.assertEqual(4, graph.report["source_objects"])
                self.assertEqual(8, graph.report["target_objects"])
                self.assertEqual(0, graph.report["skipped_objects"])
                self.assertEqual(8, len(true_objects))

                # these files are created
                self.assertEqual(
                    [
                        '/final',
                        '/final/avg152T1_LR_nifti.txt',
                        '/final/avg152T1_LR_nifti.txt.bad.json',
                        '/final/avg152T1_RL_nifti.txt',
                        '/final/avg152T1_RL_nifti.txt.bad.json',
                        '/final/avg152T1_tar',
                        '/final/avg152T1_tar/avg152T1_LR_nifti.txt',
                        '/final/avg152T1_tar/avg152T1_LR_nifti.txt.bad.json',
                        '/final/avg152T1_tar/avg152T1_RL_nifti.txt',
                        '/final/avg152T1_tar/avg152T1_RL_nifti.txt.bad.json',
                        '/final/avg152T1_tar/prefix_avg152T1_LR_nifti.nii.gz',
                        '/final/avg152T1_tar/prefix_avg152T1_LR_nifti.nii.gz.bad.json',
                        '/final/avg152T1_tar/prefix_avg152T1_RL_nifti.nii.gz',
                        '/final/avg152T1_tar/prefix_avg152T1_RL_nifti.nii.gz.bad.json',
                        '/final/prefix_avg152T1_LR_nifti.nii.gz',
                        '/final/prefix_avg152T1_LR_nifti.nii.gz.bad.json',
                        '/final/prefix_avg152T1_RL_nifti.nii.gz',
                        '/final/prefix_avg152T1_RL_nifti.nii.gz.bad.json',
                    ],
                    sorted(
                        p[len(str(tmp_dir / "target")):]
                        for p in glob.glob(str(tmp_dir / "target" / "**" / "*"), recursive=True)
                    )
                )

                target_files = list(graph.iter_target_files())
                self.assertEqual(
                    [
                        'final/avg152T1_LR_nifti.txt',
                        'final/avg152T1_RL_nifti.txt',
                        'final/avg152T1_tar/avg152T1_LR_nifti.txt',
                        'final/avg152T1_tar/avg152T1_RL_nifti.txt',
                        'final/avg152T1_tar/prefix_avg152T1_LR_nifti.nii.gz',
                        'final/avg152T1_tar/prefix_avg152T1_RL_nifti.nii.gz',
                        'final/prefix_avg152T1_LR_nifti.nii.gz',
                        'final/prefix_avg152T1_RL_nifti.nii.gz',
                    ],
                    sorted(str(t.filename) for t in target_files)
                )

                # print(json.dumps(target_files[0].data, indent=2))

                def assert_nothing_is_processed(graph):
                    true_objects = list(graph.process())
                    self.assertEqual(4, graph.report["source_objects"])
                    self.assertEqual(0, graph.report["target_objects"])
                    self.assertEqual(4, graph.report["skipped_objects"])
                    self.assertEqual(0, len(true_objects))

                # reprocessing the graph skips all processing
                assert_nothing_is_processed(graph)

                # change one of the parameters
                graph.processing_modules[-1]._parameter_values["output_x"] = 23

                # files exists so still nothing is processed
                assert_nothing_is_processed(graph)

                # touch one of the output files
                (tmp_dir / "target" / "final" / "avg152T1_LR_nifti.txt").write_text("changed it")

                assert_nothing_is_processed(graph)

                # touch one of the input files
                (tmp_dir / "source" / "avg152T1_LR_nifti.nii.gz").write_bytes(
                    (tmp_dir / "source" / "avg152T1_LR_nifti.nii.gz").read_bytes()
                )

                assert_nothing_is_processed(graph)

                # ----- switch to UNCHANGED mode -----

                graph = ModuleGraph(
                    modules=graph.modules,
                    target_path="target",
                    skip_policy=ModuleGraph.SkipPolicy.UNCHANGED,
                    log_skipping=True,
                )
                # process once to clear all previous changes
                list(graph.iter_graph_objects())

                assert_nothing_is_processed(graph)

                # change one of the parameters
                graph.processing_modules[-1]._parameter_values["output_x"] = 42

                true_objects = list(graph.process())
                self.assertEqual(4, graph.report["source_objects"])
                self.assertEqual(8, graph.report["target_objects"])
                self.assertEqual(0, graph.report["skipped_objects"])
                self.assertEqual(8, len(true_objects))

                # touch one of the output files
                (tmp_dir / "target" / "final" / "avg152T1_LR_nifti.txt").write_text("changed it")

                true_objects = list(graph.process())
                self.assertEqual(4, graph.report["source_objects"])
                self.assertEqual(2, graph.report["target_objects"])
                self.assertEqual(3, graph.report["skipped_objects"])
                self.assertEqual(2, len(true_objects))

                # touch one of the input files
                (tmp_dir / "source" / "avg152T1_LR_nifti.nii.gz").write_bytes(
                    (tmp_dir / "source" / "avg152T1_LR_nifti.nii.gz").read_bytes()
                )

                true_objects = list(graph.process())
                self.assertEqual(4, graph.report["source_objects"])
                self.assertEqual(2, graph.report["target_objects"])
                self.assertEqual(3, graph.report["skipped_objects"])
                self.assertEqual(2, len(true_objects))

                # add an object
                shutil.copy(self.DATA_PATH / "avg152T1_LR_nifti.nii.gz", tmp_dir / "source" / "new.nii.gz")

                true_objects = list(graph.process())
                self.assertEqual(5, graph.report["source_objects"])
                self.assertEqual(2, graph.report["target_objects"])
                self.assertEqual(4, graph.report["skipped_objects"])
                self.assertEqual(2, len(true_objects))

                # run again (nothing is processed)
                true_objects = list(graph.process())
                self.assertEqual(5, graph.report["source_objects"])
                self.assertEqual(0, graph.report["target_objects"])
                self.assertEqual(5, graph.report["skipped_objects"])
                self.assertEqual(0, len(true_objects))

                # run again but yield existing target objects
                existing_targets = []
                true_objects = list(graph.process(
                    existing_target_callback=lambda t: existing_targets.append(t)
                ))
                self.assertEqual(5, graph.report["source_objects"])
                self.assertEqual(0, graph.report["target_objects"])
                self.assertEqual(5, graph.report["skipped_objects"])
                self.assertEqual(0, len(true_objects))
                self.assertEqual(10, len(existing_targets))
