import os
import glob
import tempfile
import unittest
import json
from pathlib import Path
from typing import Iterable, Generator, Optional, Union

import numpy as np

from bad import config
from bad.modules import *
from tests.base import BadTestCase
# register modules
from tests.modules import testmodules


class TestModuleGraph(BadTestCase):

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

    def test_100_storage_path(self):
        graph = ModuleGraph([
            ModuleFactory.new_module("test_multi_image", parameters={"module_store_result": False}),
            ModuleFactory.new_module("image_resample", parameters={"module_store_result": True}),
            ModuleFactory.new_module("test_multi_image", parameters={"module_store_result": True}),
            ModuleFactory.new_module("image_resample", parameters={"module_store_result": True}),
            ModuleFactory.new_module(
                "test_multi_image",
                parameters={"module_store_result": True, "module_result_path": "somepath"}
            ),
            ModuleFactory.new_module("test_multi_image", parameters={"module_store_result": True}),
        ])
        paths = [
            graph.storage_paths.get(module)
            for module in graph.modules
        ]
        self.assertEqual([
            None,
            "image_resample",
            "test_multi_image",
            "image_resample2",
            "somepath",
            "test_multi_image2",
        ], paths)

    def test_200_file_source(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH,
        }):
            graph = ModuleGraph([self.create_source_module()])
            objects = list(graph.iter_source_objects())

            self.assertEqual(4, len(objects))

            object_names = [(str(o.sub_path), str(o.filename)) for o in objects]
            self.assertIn((".", "avg152T1_RL_nifti.nii.gz"), object_names)
            self.assertIn((".", "avg152T1_LR_nifti.nii.gz"), object_names)
            self.assertIn(("avg152T1_tar", "avg152T1_LR_nifti.nii.gz"), object_names)
            self.assertIn(("avg152T1_tar", "avg152T1_RL_nifti.nii.gz"), object_names)

    def test_210_file_source_recursive(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH.parent,
        }):
            graph = ModuleGraph([self.create_source_module(
                source_directory="/data",
                recursive=True,
                glob_pattern="*.nii*"
            )])
            objects = list(graph.iter_source_objects())

            object_names = [(str(o.sub_path), str(o.filename)) for o in objects]
            self.assertEqual(11, len(objects), object_names)
            self.assertIn((".", "avg152T1_RL_nifti.nii.gz"), object_names)
            self.assertIn((".", "avg152T1_LR_nifti.nii.gz"), object_names)
            self.assertIn(("subdir", "minimal.nii.gz"), object_names)

    def test_220_file_source_recursive_with_sub_path(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH.parent,
        }):
            graph = ModuleGraph([self.create_source_module(
                source_directory="/data",
                recursive=True,
                glob_pattern="*.nii*",
                sub_path="made-up",
            )])
            objects = list(graph.iter_source_objects())

            object_names = [(str(o.sub_path), str(o.filename)) for o in objects]
            self.assertEqual(11, len(objects), object_names)
            self.assertIn(("made-up", "avg152T1_RL_nifti.nii.gz"), object_names)
            self.assertIn(("made-up", "avg152T1_LR_nifti.nii.gz"), object_names)
            self.assertIn(("made-up/subdir", "minimal.nii.gz"), object_names)

    def test_300_image_source(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH,
        }):
            graph = ModuleGraph([self.create_source_module("image")])
            objects = list(graph.iter_source_objects())

            self.assertEqual(4, len(objects))

            object_names = [(str(o.sub_path), str(o.filename)) for o in objects]
            self.assertIn((".", "avg152T1_RL_nifti.nii.gz"), object_names)
            self.assertIn((".", "avg152T1_LR_nifti.nii.gz"), object_names)
            self.assertIn(("avg152T1_tar", "avg152T1_LR_nifti.nii.gz"), object_names)
            self.assertIn(("avg152T1_tar", "avg152T1_RL_nifti.nii.gz"), object_names)

            for o in objects:
                np.array(o.src.dataobj)  # make sure image data is loaded/loadable

    def test_400_multi_process(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH,
        }):
            graph = ModuleGraph([
                self.create_source_module("image"),
                ModuleFactory.new_module("test_multi_image"),
            ])
            objects = list(graph.process_objects(graph.iter_source_objects()))

            self.assertEqual(8, len(objects))

            object_names = [(str(o.sub_path), str(o.filename)) for o in objects]
            for sub_path in (".", "avg152T1_tar"):
                self.assertIn((sub_path, "sm10_avg152T1_RL_nifti.nii.gz"), object_names)
                self.assertIn((sub_path, "sm10_avg152T1_LR_nifti.nii.gz"), object_names)
                self.assertIn((sub_path, "avg152T1_RL_nifti_sm20.nii.gz"), object_names)
                self.assertIn((sub_path, "avg152T1_LR_nifti_sm20.nii.gz"), object_names)

            for o in objects:
                np.array(o.src.dataobj)  # make sure image data is loaded/loadable
                for act in o.actions:
                    if act["module"]["name"] == "test_multi_image":
                        # check that even parameter default-values are stored in actions
                        self.assertEqual(10, act["module"]["parameter_values"]["smooth_1"])
                        self.assertEqual(20, act["module"]["parameter_values"]["smooth_2"])

    def test_410_nested_multi_process(self):
        with config.ConfigOverload({
            "DATA_PATH": self.DATA_PATH,
        }):
            graph = ModuleGraph([
                self.create_source_module("image"),
                ModuleFactory.new_module("test_multi_image"),
                ModuleFactory.new_module("test_multi_image"),
            ])
            objects = list(graph.process_objects(graph.iter_source_objects()))
            self.assertEqual(16, len(objects))

            object_names = [(str(o.sub_path), str(o.filename)) for o in objects]
            for sub_path in (".", "avg152T1_tar"):
                self.assertIn((sub_path, "sm10_sm10_avg152T1_RL_nifti.nii.gz"), object_names)
                self.assertIn((sub_path, "sm10_sm10_avg152T1_LR_nifti.nii.gz"), object_names)
                self.assertIn((sub_path, "avg152T1_RL_nifti_sm20_sm20.nii.gz"), object_names)
                self.assertIn((sub_path, "avg152T1_LR_nifti_sm20_sm20.nii.gz"), object_names)
                self.assertIn((sub_path, "sm10_avg152T1_RL_nifti_sm20.nii.gz"), object_names)
                self.assertIn((sub_path, "sm10_avg152T1_LR_nifti_sm20.nii.gz"), object_names)
                self.assertIn((sub_path, "sm10_avg152T1_RL_nifti_sm20.nii.gz"), object_names)
                self.assertIn((sub_path, "sm10_avg152T1_LR_nifti_sm20.nii.gz"), object_names)

            for o in objects:
                np.array(o.src.dataobj)  # make sure image data is loaded/loadable

    def test_500_store_images_and_files(self):
        with config.ConfigOverload({
            "DATA_PATH": "/",
        }):
            with tempfile.TemporaryDirectory(prefix="bad-tests-") as tmp_dir:
                tmp_dir = Path(tmp_dir)

                graph = ModuleGraph(
                    [
                        self.create_source_module(
                            "image",
                            source_directory=self.DATA_PATH.relative_to(config.DATA_PATH),
                        ),
                        ModuleFactory.new_module("test_image_and_file"),
                        ModuleFactory.new_module("image_resample"),
                    ],
                    target_path=config.relative_to_data_path(tmp_dir),
                )

                objects = list(
                    graph.process_objects(
                        graph.iter_source_objects(),
                    )
                )

                self.assertEqual(8, len(objects))
                for o in objects:
                    if isinstance(o, ImageObject):
                        np.array(o.src.dataobj)  # make sure image data is loaded/loadable
                    elif isinstance(o, FileObject):
                        self.assertTrue(o.read_text())
                    #print(json.dumps(o.to_dict(), indent=2))

                # -- check result files on disk --
                final_dir = "image_resample"
                filenames = [
                    str(Path(fn).relative_to(tmp_dir / final_dir))
                    for fn in sorted(glob.glob(str(tmp_dir / final_dir / "**"), recursive=True))
                ]

                for path in ("", "avg152T1_tar/"):
                    for RL in ("RL", "LR"):
                        self.assertIn(f"{path}prefix_avg152T1_{RL}_nifti.nii.gz", filenames)
                        self.assertIn(f"{path}avg152T1_{RL}_nifti.txt", filenames)

                        self.assertIn(f"{path}prefix_avg152T1_{RL}_nifti.nii.gz.bad.json", filenames)
                        self.assertIn(f"{path}avg152T1_{RL}_nifti.txt.bad.json", filenames)
                
                # -- check ModuleGraph.iter_target_files --

                target_files = sorted(graph.iter_target_files())
                self.assertEqual(
                    [
                        f"{final_dir}/avg152T1_LR_nifti.txt",
                        f"{final_dir}/avg152T1_RL_nifti.txt",
                        f"{final_dir}/avg152T1_tar/avg152T1_LR_nifti.txt",
                        f"{final_dir}/avg152T1_tar/avg152T1_RL_nifti.txt",
                        f"{final_dir}/avg152T1_tar/prefix_avg152T1_LR_nifti.nii.gz",
                        f"{final_dir}/avg152T1_tar/prefix_avg152T1_RL_nifti.nii.gz",
                        f"{final_dir}/prefix_avg152T1_LR_nifti.nii.gz",
                        f"{final_dir}/prefix_avg152T1_RL_nifti.nii.gz",
                    ],
                    [str(f.filename) for f in target_files]
                )

                self.assertTrue(any(f.checksum) for f in target_files)
                self.assertTrue(any(f.data) for f in target_files)
