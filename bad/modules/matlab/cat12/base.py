import glob
import re
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import List, Union, Iterable, Generator

import nibabel

from bad import config
from bad.util.filenames import strip_compression_extension
from bad.modules.base import Module, ModuleGroup
from bad.modules.object import ModuleObjectType, ImageObject, FileObject
from bad.modules.process.image import ImageProcessModuleBase
from bad.modules.params import *


class Cat12ModuleBase(ImageProcessModuleBase):

    group = [*ImageProcessModuleBase.group, "cat12"]
    # input_types = [ModuleObjectType.FILE, ModuleObjectType.IMAGE]
    output_types = [ModuleObjectType.FILE, ModuleObjectType.IMAGE]

    # set this to True in derived class if the cat12 module supports nii.gz files
    handles_nii_gz = False

    def process_nii_files(
            self,
            input_images: Iterable[ImageObject],
            image_filenames: Iterable[Path],
            stub: bool = False,
    ) -> Generator[Union[ImageObject, FileObject], None, None]:
        """
        Override this method to call a certain CAT12 script on
        an existing `.nii` file and return the names of the
        processed images files.

        Use `self.call_cat12()` internally.
        """
        raise NotImplementedError

    @classmethod
    def cat12_version(cls) -> str:
        """
        Return the full version string
        :return: str, something like "12.8.1_r2042"
        """
        # TODO: Currently requires the version to be in the path
        #   Need to find the place within the package where the version is defined
        path = str(config.CAT12_PATH)
        match = re.match(r".*CAT([\d.]+_r[\d]+)", path)
        if match:
            return match.groups()[0]
        return "UNKNOWN"

    @classmethod
    def class_to_dict(cls) -> dict:
        ret = super().class_to_dict()
        ret["cat12_version"] = cls.cat12_version()
        return ret

    def process_objects(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:
        yield from self.process_images(images, stub=stub)

    def process_images(
            self,
            images: Iterable[ImageObject],
            stub: bool = False
    ) -> Generator[ImageObject, None, None]:

        temp_path = config.TEMP_PATH / f"module-cat12-{secrets.token_hex(20)}"
        if not stub:
            os.makedirs(temp_path)

        try:
            for image in images:
                # TODO: need to convert to .nii (or nii.gz) if image.filename is not .nii
                temp_image_name = temp_path / strip_compression_extension(image.filename)
                if not stub:
                    image.src.to_filename(temp_image_name)

                # TODO: it's possible to bundle a few images to
                #   speed up the processing
                yield from self.process_nii_files([image], [temp_image_name], stub=stub)

        finally:
            if not stub:
                shutil.rmtree(temp_path, ignore_errors=True)

    def call_cat12(
            self,
            script_name: str,
            *args: str,
            parameters: Optional[dict] = None,
    ):
        temp_path = config.TEMP_PATH / f"module-cat12-{secrets.token_hex(20)}"

        try:
            script_filename = config.CAT12_PATH / "standalone" / f"{script_name}.m"

            if parameters:
                os.makedirs(temp_path)
                script = script_filename.read_text()
                patched_script = self._patch_script(script, parameters)
                script_filename = config.TEMP_PATH / f"patched_{script_name}.m"
                script_filename.write_text(patched_script)

            full_args = [
                config.CAT12_PATH / "standalone" / "cat_standalone.sh",
                "-m", config.MATLAB_PATH,
                "-b", script_filename,
                *args,
            ]

            subprocess.check_call(full_args)

        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    def _patch_script(self, script: str, parameters: dict) -> str:
        script_lines = script.splitlines()
        for name, value in parameters.items():

            expr = re.compile(r"^matlabbatch\{1}." + name + r"\s*=\s*.*")

            line_to_replace = None
            for i, line in enumerate(script_lines):
                match = expr.match(line)
                if match:
                    line_to_replace = i
                    break

            if not line_to_replace:
                raise ValueError(f"Could not override variable '{name}'")

            if isinstance(value, bool):
                value = 1 if value else 0
            elif isinstance(value, str):
                value = f"'{value}'"
            elif value == float("-inf"):
                value = "-Inf"

            script_lines[line_to_replace] = f"matlabbatch{{1}}.{name} = {value};"

        return "\n".join(script_lines)
