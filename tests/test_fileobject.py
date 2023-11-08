import unittest
from pathlib import Path
import tarfile
from io import BytesIO

from bad import config
from bad.modules import *


FILENAME_IXI_T1 = Path("~/prog/data/datasets/ixi/IXI-T1.tar").expanduser()


class TestFileObject(unittest.TestCase):

    def test_image_format(self):
        self.assertTrue(filename_matches_supported_image_formats("bla/blub.nii"))
        self.assertTrue(filename_matches_supported_image_formats("bla/blub.nii.gz"))
        self.assertTrue(filename_matches_supported_image_formats("bla/blub.nii.bz2"))

        self.assertFalse(filename_matches_supported_image_formats("bla/blub.nii.zip"))

    def test_disk_file(self):
        full_path = Path(__file__).resolve()
        with config.ConfigOverload({
            "DATA_PATH": full_path.parent.parent
        }):
            obj = FileObjectDisk(full_path.name, "", "tests")
            self.assertTrue(
                obj.read_text().startswith("import unittest"),
                f"Got: {obj.read_text()}"
            )

    def test_tar_file(self):
        CONTENT = b"a sequence of ascii compatible bytes"
        tar_filename = "/tmp/tarfile.tar"
        with config.ConfigOverload({
                "DATA_PATH": "/",
        }):
            with tarfile.open(tar_filename, "w") as tf:

                for i in range(3):
                    content = BytesIO(CONTENT)
                    info = tarfile.TarInfo(f"file{i}.bin")
                    info.size = len(CONTENT)
                    tf.addfile(info, content)

            for i, obj in enumerate(FileObjectTar.iter_file_objects(tar_filename)):
                self.assertEqual(f"file{i}.bin", obj.filename)
                self.assertEqual(CONTENT, obj.read_bytes())

    @unittest.skipIf(not FILENAME_IXI_T1.exists(), f"missing file {FILENAME_IXI_T1}")
    def test_ixi_t1(self):
        i = 0
        for i, obj in enumerate(FileObjectTar.iter_file_objects(FILENAME_IXI_T1)):
            with obj.open(uncompressed=False):
                pass
        self.assertEqual(580, i)

    def test_file_object_memory(self):
        obj = FileObjectMemory(
            content="Some UTF-8 content",
            filename="filename.txt",
            sub_path="sub_path",
            source_path="source_path",
            actions=[{"name": "action1"}],
            source={"some": "source"},
        )
        data = obj.to_dict()
        self.assertEqual("Some UTF-8 content", obj.content)
        self.assertEqual("filename.txt", obj.filename)
        self.assertEqual(Path("sub_path"), obj.sub_path)
        self.assertEqual(Path("source_path"), obj.source_path)
        self.assertEqual([{"name": "action1"}], data["actions"])
        self.assertEqual({"some": "source"}, data["source"])

