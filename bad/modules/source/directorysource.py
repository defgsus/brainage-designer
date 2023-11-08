from pathlib import Path
import glob
from typing import Generator, Union

from bad import config
from ..object.base import ModuleObjectType
from ..object.fileobject import FileObjectDisk, FileObjectTar
from ..params import *
from .file import FileSourceModuleBase


class FileSourceDirectoryModule(FileSourceModuleBase):

    name = "file_source_directory"
    output_types = [ModuleObjectType.FILE]

    parameters = [
        ParameterFilepath(
            name="source_directory",
            description="The directory containing the source files",
            default_value="/",
        ),
        ParameterString(
            name="glob_pattern",
            description="The globbing pattern to search for files",
            default_value="*",
        ),
        ParameterBool(
            name="recursive",
            description="Recursively scan sub-directories",
            default_value=False,
        ),
        ParameterBool(
            name="traverse_tar",
            description="Traverse into tar files?",
            default_value=False,
        ),
        *FileSourceModuleBase.parameters,
    ]

    def get_object_count(self) -> int:
        local_path = self.get_parameter_value("source_directory")
        global_path = config.join_data_path(local_path)
        recursive = self.get_parameter_value("recursive")
        traverse_tar = self.get_parameter_value("traverse_tar")
        glob_pattern = self.get_parameter_value("glob_pattern")
        if recursive and "**" not in glob_pattern:
            glob_pattern = Path("**") / glob_pattern

        num_objects = 0
        for global_filename in glob.iglob(str(global_path / glob_pattern), recursive=recursive):
            filename = Path(global_filename).relative_to(global_path)

            has_yielded = False
            if traverse_tar:
                fn_low = filename.name.lower()
                if fn_low.endswith(".tar") or fn_low.endswith(".tar.gz"):
                    num_objects += FileObjectTar.get_file_count(global_filename)
                    has_yielded = True

            if not has_yielded:
                num_objects += 1

        return num_objects

    def iter_objects(
            self,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
    ) -> Generator[FileObjectDisk, None, None]:
        assert interval >= 1, f"interval must be >= 1, got {interval}"

        local_path = self.get_parameter_value("source_directory")
        global_path = config.join_data_path(local_path)
        object_sub_path = self.get_parameter_value("module_object_sub_path")
        recursive = self.get_parameter_value("recursive")
        traverse_tar = self.get_parameter_value("traverse_tar")
        glob_pattern = self.get_parameter_value("glob_pattern")
        if recursive and "**" not in glob_pattern:
            glob_pattern = Path("**") / glob_pattern

        index = offset
        for global_filename in glob.iglob(str(global_path / glob_pattern), recursive=recursive):
            # ignore own status files
            if global_filename.endswith(".bad.json"):
                continue

            if index % interval == 0:

                filename = Path(global_filename).relative_to(global_path)

                has_yielded = False
                if traverse_tar:
                    fn_low = filename.name.lower()
                    if fn_low.endswith(".tar") or fn_low.endswith(".tar.gz"):
                        # TODO: unfortunately we can not easily pass the interval/offset settings
                        #   to this generator. Probably need to process tar files separately
                        #   and not within this single-file loop
                        yield from FileObjectTar.iter_file_objects(
                            global_filename,
                            module=self,
                        )
                        has_yielded = True

                if not has_yielded:
                    sub_path = filename.parent
                    if object_sub_path:
                        sub_path = object_sub_path / sub_path

                    yield FileObjectDisk(
                        filename=Path(filename).name,
                        sub_path=sub_path,
                        source_path=local_path / filename.parent,
                        actions=[
                            self.action_dict(
                                action_name="loaded",
                                filename=str(Path(local_path) / filename),
                                mtime=Path(global_filename).stat().st_mtime_ns,
                            ),
                        ],
                    )

            index += 1
