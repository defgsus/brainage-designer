import os
import unittest
from functools import wraps
from pathlib import Path
from typing import Generator, Dict, Any, Optional, Union

import nibabel

from bad import config
from bad.modules import ImageObject, FileObjectTar


class BadTestCase(unittest.TestCase):

    DATA_PATH: Path = config.BASE_PATH / "tests" / "data"

    @classmethod
    def tag_long(cls):
        return unittest.skipIf(not os.environ.get("BAD_TEST_LONG"), "BAD_TEST_LONG not defined")

    @classmethod
    def tag_server(cls):
        return unittest.skipIf(not os.environ.get("BAD_TEST_SERVER"), "BAD_TEST_SERVER not defined")

    def load_image_object(
            self,
            filename: str,
            sub_path: Optional[Union[str, Path]] = None,
    ) -> ImageObject:
        """
        Load an image from `<project>/tests/data/<filename>`
        """
        return ImageObject(
            src=nibabel.load(
                self.DATA_PATH / filename,
            ),
            filename=filename,
            sub_path=sub_path,
            source_path="",
        )

    def iter_tar_objects(self, filename: str) -> Generator[FileObjectTar, None, None]:
        """
        Load an image from `<project>/tests/data/<filename>`
        """
        yield from FileObjectTar.iter_file_objects(
            config.BASE_PATH / "tests" / "data" / filename,
        )
