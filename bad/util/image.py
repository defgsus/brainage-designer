from typing import Optional, Tuple, Sequence, Union

import numpy as np
from nilearn import image as niimage
from nibabel.filebasedimages import SerializableImage
import PIL.Image


def get_image_slice(nibabel_image, axis: int = 0, offset: Optional[int] = None):
    slice_args = [slice(None) for i in range(nibabel_image.ndim)]
    if offset is None:
        offset = nibabel_image.shape[axis] // 2
    slice_args[axis] = slice(offset, offset+1)
    brain_slice = nibabel_image.slicer[slice_args[0], slice_args[1], slice_args[2]]
    layer = brain_slice.get_fdata()
    return layer.squeeze()


def np_to_pil(np_array: np.ndarray) -> PIL.Image.Image:
    img = (np_array / np_array.max() * 255).astype(np.int8)[::-1, :]
    return PIL.Image.fromarray(img, mode="L")


def resample_to_shape(img, shape: Tuple[int, int, int], interpolation: str = "continuous"):
    new_affine = img.affine * np.array([
        img.shape[-3] / shape[-3],
        img.shape[-2] / shape[-2],
        img.shape[-1] / shape[-1],
        1
    ])
    return niimage.resample_img(
        img,
        target_shape=shape,
        target_affine=new_affine,
        interpolation=interpolation,
    )


def get_volume_slices(
        volume: np.ndarray,
        offsets: Optional[Sequence[Optional[int]]] = None,
        join_axis: int = 1,
) -> np.ndarray:
    assert join_axis in (0, 1), f"join_axis must be 0 or 1, got {join_axis}"

    max_shape = max(*volume.shape)
    max_value = np.max(volume)
    planes = []
    for axis in range(len(volume.shape)):
        slice_args = [slice(None) for a in range(len(volume.shape))]
        if not offsets or offsets[axis] is None:
            slice_args[axis] = volume.shape[axis] // 2
        else:
            slice_args[axis] = offsets[axis]

        plane = volume[tuple(slice_args)]

        if join_axis == 0:
            padding_width = (
                (0, 1),
                (0, max_shape - plane.shape[1])
            ),
        else:
            padding_width = (
                (0, max_shape - plane.shape[0]),
                (0, 1),
            )
        plane = np.pad(
            plane,
            pad_width=padding_width,
            constant_values=max_value / 3.,
        )
        planes.append(plane)

    planes = np.concatenate(planes, axis=join_axis)
    return planes


def to_target_shape(array: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    if len(array.shape) != len(shape):
        raise ValueError(f"Dimension mismatch, array has {len(array.shape)}, shape has {len(shape)}")
    if array.shape == shape:
        return array

    slice_args = []
    needs_shrink = False
    for expected, real in zip(shape, array.shape):
        if real > expected:
            slice_args.append(slice(0, expected))
            needs_shrink = True
        else:
            slice_args.append(slice(None, None))

    if needs_shrink:
        array = array[tuple(slice_args)]

    pad_args = []
    needs_pad = False
    for expected, real in zip(shape, array.shape):
        if real < expected:
            pad_args.append((0, expected - real))
            needs_pad = True
        else:
            pad_args.append((0, 0))

    if needs_pad:
        array = np.pad(array, pad_width=pad_args)

    return array


def to_output_dtype(data: np.ndarray, dtype: Union[str, np.dtype]) -> np.ndarray:
    dtype = str(dtype)
    real_dtype = str(data.dtype)
    if dtype == real_dtype:
        return data

    if dtype in ("float32", "float64"):
        return data.astype(dtype)

    elif dtype == "uint8":
        mi, ma = np.min(data), np.max(data)
        if mi >= 0:
            if ma:
                data = data / ma
        else:
            if (mi - ma):
                data = (data - mi) / (ma - mi)

        return (data * 255).astype(dtype)

    else:
        raise ValueError(f"Unsupported dtype '{dtype}'")


def nibabel_to_numpy_float(src: SerializableImage) -> np.ndarray:
    org_dtype = src.get_data_dtype()
    data = src.get_fdata()

    if org_dtype.name == "int16":
        data /= (2 * 16)

    elif org_dtype.name == "int8":
        data /= (2 * 8)

    return to_output_dtype(data, "float32")
