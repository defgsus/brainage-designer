import tempfile
from pathlib import Path

import nibabel
import numpy as np

from bad.modules import ImageObject, FileObject, FileObjectTar
from tests.base import BadTestCase


class TestImageObject(BadTestCase):

    def test_image(self):
        image = self.load_image_object("avg152T1_LR_nifti.nii.gz")

        data: np.ndarray = image.src.get_fdata()
        self.assertTrue(np.sum(data.flatten()))

    def test_image_from_tar(self):
        for tar_obj in self.iter_tar_objects("avg152T1.tar"):
            image = tar_obj.read_nibabel()

            data: np.ndarray = image.src.get_fdata()
            self.assertTrue(np.sum(data.flatten()))

    def test_image_only_in_memory(self):
        image = self.load_image_object("avg152T1_LR_nifti.nii.gz")

        # simulate a processing step that is run in a temporary directory
        #   and reads the resulting image into memory
        with tempfile.TemporaryDirectory(prefix="bad-tests") as tmp_dir:
            tmp_name = Path(tmp_dir) / "test.nii"
            image.src.to_filename(tmp_name)

            image = image.replace(
                {"name": "some action"},
                src=tmp_name,
            )

        # data still there!
        data: np.ndarray = np.array(image.src.dataobj)
        self.assertTrue(np.sum(data.flatten()))
