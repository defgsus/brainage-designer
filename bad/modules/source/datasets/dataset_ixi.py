from pathlib import Path
from typing import Generator

import nibabel
import numpy

from bad import config
from ..image import ImageSourceModuleBase, ImageObject
from ...object import FileObjectTar
from ...params import *
from bad.util.downloader import streaming_download


class DatasetIxi(ImageSourceModuleBase):
    name = "dataset_ixi"
    output_types = ["image"]

    BASE_URL = "https://biomedic.doc.ic.ac.uk/brain-development/downloads/IXI"

    parameters = [
        ParameterSelect(
            name="dataset",
            default_value="T1",
            description="Select the dataset / modality",
            options=(
                ParameterSelect.Option("T1", "T1 modality"),
                ParameterSelect.Option("T2", "T2 modality"),
                ParameterSelect.Option("MRA", "MRA modality"),
                ParameterSelect.Option("PD", "PD modality"),
                ParameterSelect.Option("DTI", "DTI modality"),
            ),
        ),
        ParameterFilepath(
            name="local_path",
            default_value="/prog/data/datasets/ixi/",
            description="Local directory to store the files",
        ),
        *ImageSourceModuleBase.parameters,
    ]

    def get_object_count(self) -> int:
        return 581

    def dataset_url(self) -> str:
        return f"{self.BASE_URL}/IXI-{self.get_parameter_value('dataset')}.tar"

    def dataset_meta_url(self) -> str:
        return f"{self.BASE_URL}/IXI.xls"

    def local_path(self) -> Path:
        return Path(config.join_data_path(self.get_parameter_value("local_path")))

    def local_tar_name(self) -> Path:
        return self.local_path() / f"IXI-{self.get_parameter_value('dataset')}.tar"

    def local_meta_name(self) -> Path:
        return self.local_path() / f"IXI.xls"

    def prepare(self):
        streaming_download(
            url=self.dataset_url(),
            filename=self.local_tar_name(),
        )
        streaming_download(
            url=self.dataset_meta_url(),
            filename=self.local_meta_name(),
        )

    def iter_objects(
            self,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,

    ) -> Generator[ImageObject, None, None]:
        for i, obj in enumerate(FileObjectTar.iter_file_objects(
                self.local_tar_name(),
                interval=interval, offset=offset,
                module=self,
                stub=stub,
        )):
            yield obj.read_nibabel(stub=stub)
