from pathlib import Path
import os
import glob
from io import BytesIO
from typing import Optional, Iterable, Union

import nibabel
import PIL.Image
import numpy as np
import nilearn.plotting

from bad import config
from bad.plugins import PluginBase
from bad.server.handlers import JsonBaseHandler, DbRestHandler, BaseHandler
from bad.modules import *
from bad.util.image import get_image_slice, np_to_pil, get_volume_slices
from bad.util.table import read_table


class FileBrowserPlugin(PluginBase):
    name = "files"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_image = None

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/api/files/browse/", BrowserHandler),
            (r"/api/files/image/meta/", ImageMetaHandler),
            (r"/api/files/image/slice/", ImageSliceHandler),
            (r"/api/files/image/slices/", ImageSlicesHandler),
            (r"/api/files/image/plot/", ImagePlotHandler),
            (r"/api/files/image/blob/", ImageHandler),
            (r"/api/files/table/", TableHandler),
        ]

    def get_file_object(self, path: str) -> Union[FileObjectDisk, FileObjectMemory]:
        """
        Returns a FileObject from a path
        :param path: str,
            path relative to `config.DATA_PATH`
            The path can contain a tar filename, in which case the remaining
            path is treated as the member of the tar file. e.g. "path/compressed.tar/member.txt"

        :return: a readable FileObject
        """
        segments = os.path.split(path)

        disk_segments = []
        tar_segments = []
        is_tar = False
        for seg in segments:
            if not is_tar:
                disk_segments.append(seg)
            else:
                tar_segments.append(seg)

            if seg.lower().endswith(".tar") or seg.lower().endswith(".tar.gz"):
                is_tar = True

        disk_path = Path(os.path.join(*disk_segments))

        if not tar_segments:
            return FileObjectDisk(
                filename=disk_path.name,
                sub_path="",
                source_path=disk_path.parent,
            )

        else:
            member_name = os.path.join(*tar_segments)

            return FileObjectMemory.from_tar_member(
                tar_filename=disk_path,
                member_name=member_name,
            )

    def get_image_object(self, path: str) -> Optional[ImageObject]:
        """
        Returns an ImageObject

        :param path: str, sames rules as for `get_file_object`

        :return: None if file not found, or an ImageObject

        Raises error when image is not readable
        """
        if not self._cached_image or self._cached_image[0] != path:
            try:
                file = self.get_file_object(path)
            except:
                file = None

            if file is not None:
                file = file.read_nibabel()

            self._cached_image = (path, file)

        return self._cached_image[1]


class BrowserHandler(JsonBaseHandler):

    def get(self):
        complete_path = self.get_query_argument("path").lstrip("/")
        recursive = bool(self.get_query_argument("recursive", default=""))
        complete_paths = f"/{complete_path}".split(os.path.sep)

        if not recursive:
            root_response = self._scan_path(config.DATA_PATH / complete_path)

        else:
            response = root_response = {}

            full_path = config.DATA_PATH
            for i, sub_path in enumerate(complete_paths):

                data = self._scan_path(full_path / sub_path)
                response.update(data)

                follow = False
                if i < len(complete_paths) - 1:
                    next_sub_path = complete_paths[i + 1]
                    for dir_entry in data["dirs"]:
                        if dir_entry["name"] == next_sub_path:
                            dir_entry["open"] = True
                            dir_entry["children"] = response = {}
                            full_path = full_path / sub_path
                            follow = True
                            break

                if not follow:
                    break

        self.write(root_response)

    def _scan_path(self, full_path: Path) -> dict:
        try:
            all_entries = os.scandir(full_path)
            all_entries = sorted(
                filter(lambda e: not e.name.startswith("."), all_entries),
                key=lambda e: e.name.lower()
            )
        except FileNotFoundError:
            all_entries = []

        relative_path = full_path.relative_to(config.DATA_PATH)

        data = {
            "path": "/" if str(relative_path) == "." else f"/{relative_path}",
            "files": [],
            "dirs": [],
        }
        for e in all_entries:
            if e.is_dir():
                data["dirs"].append({
                    "path": f"/{relative_path / e.name}",
                    "name": e.name,
                })
            else:
                entry = {
                    "name": e.name,
                }
                if filename_matches_supported_image_formats(e.name):
                    entry["type"] = "image"
                data["files"].append(entry)

        return data


class ImageMetaHandler(JsonBaseHandler):

    def get(self):
        path = self.get_query_argument("path")

        try:
            image: ImageObject = self.plugin.get_image_object(path)
            if not image:
                self.set_status(404)
                self.write({"detail": "Not found"})
                return

            self.write({
                "path": path,
                "shape": image.shape,
                "dtype": str(image.dtype),
                "range": [np.min(image.src.dataobj), np.max(image.src.dataobj)],
                "voxel_size": image.voxel_size,
            })

        except Exception as e:
            self.set_status(500)
            self.write({"detail": f"{type(e).__name__}: {e}"})
            return


class ImageSliceHandler(BaseHandler):

    def get(self):
        path = self.get_query_argument("path")

        try:
            image: ImageObject = self.plugin.get_image_object(path)
            if not image:
                self.set_status(404)
                self.write({"detail": "Not found"})
                return
        except Exception as e:
            self.set_status(500)
            self.write({"detail": f"{type(e).__name__}: {e}"})
            return

        axis = self.get_query_argument("axis", "0")
        try:
            axis = int(axis)
        except (ValueError, TypeError):
            axis = 0

        offset = self.get_query_argument("offset", "")
        try:
            offset = int(offset)
        except (ValueError, TypeError):
            offset = None

        slice = get_image_slice(image.src, axis=axis, offset=offset)
        pil_image = np_to_pil(slice)

        fp = BytesIO()
        pil_image.save(fp, "png")
        fp.seek(0)

        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.set_header("Content-Type", "image/png")
        self.write(fp.read())


class ImageSlicesHandler(BaseHandler):

    def get(self):
        path = self.get_query_argument("path")

        try:
            image: ImageObject = self.plugin.get_image_object(path)
            if not image:
                self.set_status(404)
                self.write({"detail": "Not found"})
                return
        except Exception as e:
            self.set_status(500)
            self.write({"detail": f"{type(e).__name__}: {e}"})
            return

        offsets = []
        for axis in range(len(image.shape)):
            try:
                offset = int(self.get_query_argument(f"o{axis}", None))
            except (ValueError, TypeError):
                offset = None
            offsets.append(offset)

        planes = get_volume_slices(image.src.get_fdata(), offsets=offsets)
        pil_image = np_to_pil(planes)

        fp = BytesIO()
        pil_image.save(fp, "png")
        fp.seek(0)

        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.set_header("Content-Type", "image/png")
        self.write(fp.read())


class ImagePlotHandler(BaseHandler):

    def get(self):
        path = self.get_query_argument("path")

        try:
            image: ImageObject = self.plugin.get_image_object(path)
            if not image:
                self.set_status(404)
                self.write({"detail": "Not found"})
                return
        except Exception as e:
            self.set_status(500)
            self.write({"detail": f"{type(e).__name__}: {e}"})
            return

        fp = BytesIO()

        plot_type = self.get_query_argument("plot", "epi")
        if plot_type == "anat":
            nilearn.plotting.plot_anat(
                image.src,
                output_file=fp,
            )
        elif plot_type == "glass_brain":
            nilearn.plotting.plot_glass_brain(
                image.src,
                output_file=fp,
            )
        else:
            nilearn.plotting.plot_epi(
                image.src,
                output_file=fp,
            )

        fp.seek(0)
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.set_header("Content-Type", "image/png")
        self.write(fp.read())


class ImageHandler(BaseHandler):

    def get(self):
        path = self.get_query_argument("path")

        try:
            image: ImageObject = self.plugin.get_image_object(path)
            if not image:
                self.set_status(404)
                self.write({"detail": "Not found"})
                return
        except Exception as e:
            self.set_status(500)
            self.write({"detail": f"{type(e).__name__}: {e}"})
            return

        try:
            data = image.src.get_fdata().astype("float32")

            # mi, ma = data.min(), data.max()
            # if mi != ma:
            #     data = (data - mi) / (ma - mi)

            data_range = [data.min(), data.max()]

            data_zooms = image.voxel_size

        except Exception as e:
            self.set_status(500)
            self.write(f"Error: {e}")
            return

        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.set_header("Content-Type", "text/plain; charset=x-user-defined")
        self.set_header(
            "X-Image-Meta",
            f'{",".join(str(s) for s in data.shape)}'
            f';{",".join(str(s) for s in data_zooms)}'
            f';{",".join(str(s) for s in data_range)}'
            f';{str(data.dtype)}'
        )
        self.write(data.tobytes())


class TableHandler(JsonBaseHandler):

    def get(self):
        local_path = self.get_query_argument("path")
        global_path = config.DATA_PATH / local_path.lstrip("/")

        try:
            rows = read_table(global_path)
            self.write({
                "file": local_path,
                "rows": rows,
            })
        except Exception as e:
            self.write({"error": f"{type(e).__name__}: {e}"})
            self.set_status(500)
