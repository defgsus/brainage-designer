from pathlib import Path
import tarfile
import gzip
import bz2
from io import StringIO, BytesIO
from typing import Optional, Generator, IO, Union, List

from nibabel import FileHolder, all_image_classes
from nibabel.filebasedimages import ImageFileError

from bad import config
from bad.util.filenames import add_to_filename, strip_extension, strip_compression_extension
from .base import ModuleObject, ModuleObjectType
from .imageobject import ImageObject


class FileObject(ModuleObject):
    data_type = ModuleObjectType.FILE

    supported_compression_exts = (".gz", ".bz2")

    def __init__(
            self,
            filename: str,
            sub_path: Union[str, Path],
            source_path: Union[str, Path],
            actions: Optional[List[dict]] = None,
            source: Optional[dict] = None,
    ):
        super().__init__(actions=actions, source=source)
        self.filename: str = str(filename)
        self.sub_path: Path = Path(str(sub_path).rstrip("/"))
        self.source_path: Path = Path(str(source_path).rstrip("/"))

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(str(self.sub_path))}, {repr(str(self.filename))})"

    @property
    def true_filename(self) -> Path:
        return config.join_data_path(self.source_path) / self.filename

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "filename": str(self.filename),
            "sub_path": str(self.sub_path),
            "source_path": str(self.source_path),
        }

    @property
    def compression_suffix(self) -> Optional[str]:
        name = self.filename.lower()
        for suffix in self.supported_compression_exts:
            if name.endswith(suffix):
                return suffix

    def open(self, mode: str = "rb", uncompressed: bool = True) -> IO:
        raise NotImplementedError

    def open_gzip(self, mode: str = "rb") -> IO:
        return gzip.GzipFile(
            mode=mode,
            fileobj=self.open(mode, uncompressed=False),
        )

    def open_bz2(self, mode: str = "rb") -> IO:
        return bz2.BZ2File(self.open(mode, uncompressed=False))

    def read_bytes(self, uncompressed: bool = True) -> bytes:
        raise NotImplementedError

    def read_text(
            self,
            encoding: Optional[str] = None,
            errors: Optional[str] = None,
            uncompressed: bool = True,
    ) -> str:
        kwargs = {}
        if encoding:
            kwargs["encoding"] = encoding
        if errors:
            kwargs["errors"] = errors
        return self.read_bytes().decode(**kwargs)

    def read_nibabel(self, stub: bool = False) -> Optional[ImageObject]:
        """
        Try to load the file as image.
        Returns None if the filename does not match any format

        If `stub == True` return an ImageObject with a dummy image
        instead of loading the file.
        """
        # This rebuilds the `nibabel.load()` function a bit
        #   because it doesn't seem to support reading from
        #   file objects right away
        filename_lower = str(self.filename).lower()
        for image_klass in all_image_classes:

            matches = False
            for ext in image_klass.valid_exts:
                for suffix in ("", ) + image_klass._compressed_suffixes:
                    ext = ext + suffix
                    if filename_lower.endswith(ext):
                        matches = True
                        break

            if matches:
                if stub:
                    img = ImageObject.STUB_IMAGE
                else:
                    img = image_klass.from_bytes(self.read_bytes(uncompressed=True))

                return ImageObject(
                    img,
                    filename=self.filename,
                    sub_path=self.sub_path,
                    source_path=self.source_path,
                    actions=self.actions,
                )

    def replace(
            self,
            action: dict,
            filename: Optional[str] = None,
            filename_prefix: Optional[str] = None,
            filename_suffix: Optional[str] = None,
            sub_path: Optional[Union[str, Path]] = None,
            **kwargs,
    ) -> "FileObject":
        """
        Replace the filename and store an action.

        :param action: a dict with at least a `name` property
        :return: new FileObject instance
        """
        filename = str(self.filename if filename is None else filename)
        filename = add_to_filename(filename, filename_prefix, filename_suffix)

        new_obj = self.__class__(
            filename=filename,
            sub_path=self.sub_path if sub_path is None else sub_path,
            source_path=self.source_path,
            actions=self.actions + [action],
            **kwargs,
        )
        new_obj.source = self.source or self.to_dict()
        return new_obj


class FileObjectDisk(FileObject):

    def open(self, mode: str = "rb", uncompressed: bool = True):
        if not uncompressed:
            return open(self.true_filename, mode)

        compression = self.compression_suffix
        if compression == ".gz":
            return self.open_gzip(mode)
        elif compression == ".bz2":
            return self.open_bz2(mode)
        else:
            return self.open(mode, uncompressed=False)

    def read_bytes(self, uncompressed: bool = True) -> bytes:
        if uncompressed and self.compression_suffix:
            with self.open("rb") as fp:
                return fp.read()

        return self.true_filename.read_bytes()

    def read_text(
            self,
            encoding: Optional[str] = None,
            errors: Optional[str] = None,
            uncompressed: bool = True,
    ) -> str:
        if uncompressed and self.compression_suffix:
            return self.read_bytes().decode(encoding=encoding, errors=errors)
        return self.true_filename.read_text(encoding=encoding, errors=errors)


class FileObjectTar(FileObject):

    def __init__(
            self,
            tarfile: tarfile.TarFile,
            filename: str,
            sub_path: Union[str, Path],
            source_path: Union[str, Path],
            actions: Optional[List[dict]] = None
    ):
        super().__init__(filename=filename, sub_path=sub_path, source_path=source_path, actions=actions)
        self._tarfile = tarfile

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "tar_filename": self._tarfile.name,
        }

    def open(self, mode: str = "rb", uncompressed: bool = True):
        if mode not in ("rb", ):
            raise NotImplementedError(f"Mode '{mode}' for tar currently not supported")

        if not uncompressed:
            return self._tarfile.extractfile(str(self.filename))

        compression = self.compression_suffix
        if compression == ".gz":
            return self.open_gzip(mode)
        elif compression == ".bz2":
            return self.open_bz2(mode)
        else:
            return self.open(mode, uncompressed=False)

    def read_bytes(self, uncompressed: bool = True) -> bytes:
        with self.open(uncompressed=uncompressed) as fp:
            return fp.read()

    @classmethod
    def iter_file_objects(
            cls,
            tar_filename: Union[str, Path],
            interval: int = 1,
            offset: int = 0,
            module: Optional["Module"] = None,
            stub: bool = False,
    ) -> Generator["FileObjectTar", None, None]:
        assert interval >= 1, f"interval must be >= 1, got {interval}"

        tar_path = config.relative_to_data_path(Path(tar_filename))
        tar_name = f"{strip_extension(strip_compression_extension(tar_path.name))}_tar"

        index = offset
        tar_mtime = Path(tar_filename).stat().st_mtime_ns
        with tarfile.open(tar_filename) as tf:
            for member in tf.getmembers():
                if index % interval == 0:

                    actions = None
                    if module:
                        actions = [
                            module.action_dict(
                                action_name="loaded",
                                filename=str(tar_path / member.name),
                                mtime=tar_mtime,
                            ),
                        ]

                    yield cls(
                        tarfile=tf,
                        filename=member.name,
                        sub_path=tar_name,
                        source_path=tar_path.parent,
                        actions=actions,
                    )
                index += 1

    @classmethod
    def get_file_count(
            cls,
            tar_filename: Union[str, Path],
    ) -> int:
        with tarfile.open(tar_filename) as tf:
            return len(tf.getmembers())


class FileObjectMemory(FileObject):

    def __init__(
            self,
            content: Union[str, bytes],
            filename: str,
            sub_path: Union[str, Path],
            source_path: Union[str, Path],
            actions: Optional[List[dict]] = None,
            source: Optional[dict] = None,
    ):
        super().__init__(
            filename=filename,
            sub_path=sub_path,
            source_path=source_path,
            actions=actions,
            source=source,
        )
        self.content = content

    @classmethod
    def from_tar_member(
            cls,
            tar_filename: Union[str, Path],
            member_name: Union[str, Path],
    ) -> "FileObjectMemory":
        global_tar_filename = config.join_data_path(tar_filename)
        with tarfile.open(global_tar_filename) as tf:
            content = tf.extractfile(member_name).read()
            return cls(
                content=content,
                filename=member_name,
                sub_path=f"{strip_extension(strip_compression_extension(global_tar_filename.name))}_tar",
                source_path=Path(tar_filename).parent,
            )

    def replace(
            self,
            action: dict,
            content: Optional[Union[str, bytes]] = None,
            filename: Optional[str] = None,
            filename_prefix: Optional[str] = None,
            filename_suffix: Optional[str] = None,
            sub_path: Optional[Union[str, Path]] = None,
    ) -> "FileObjectMemory":
        return super().replace(
            action=action,
            content=content if content is not None else self.content,
            filename=filename,
            filename_prefix=filename_prefix,
            filename_suffix=filename_suffix,
            sub_path=sub_path,
        )

    def open(self, mode: str = "rb", uncompressed: bool = True):
        assert mode == "rb", f"Sorry, mode '{mode}' currently not supported for {self}"

        if not uncompressed:
            if isinstance(self.content, str):
                return StringIO(self.content)
            else:
                return BytesIO(self.content)

        compression = self.compression_suffix
        if compression == ".gz":
            return self.open_gzip(mode)
        elif compression == ".bz2":
            return self.open_bz2(mode)
        else:
            return self.open(mode, uncompressed=False)

    def read_bytes(self, uncompressed: bool = True) -> bytes:
        if uncompressed and self.compression_suffix:
            with self.open("rb") as fp:
                return fp.read()

        if isinstance(self.content, str):
            return self.content.encode()
        return self.content

    def read_text(
            self,
            encoding: Optional[str] = None,
            errors: Optional[str] = None,
            uncompressed: bool = True,
    ) -> str:
        if uncompressed and self.compression_suffix:
            return self.read_bytes().decode(encoding=encoding, errors=errors)
        if isinstance(self.content, str):
            return self.content
        return self.content.decode(encoding=encoding, errors=errors)
