from typing import Iterable

import numpy as np


class NumpyIterable:
    """
    Container for `np.ndarray`s, all of which have the same shape.
    """
    def __init__(self, iterable: Iterable[np.ndarray], num_arrays: int):
        self._iterable = iterable
        self._num_arrays = num_arrays

    def __iter__(self):
        return self._iterable

    def __len__(self):
        return self._num_arrays

    def concat(self, flat: bool = False) -> np.ndarray:
        """
        Concatenate the arrays in a memory-efficient way
        """
        matrix = None
        for idx, a in enumerate(self._iterable):

            if flat:
                a = a.reshape(-1)

            if matrix is None:
                matrix = np.ndarray((self._num_arrays, *a.shape), dtype=a.dtype)

            else:
                assert a.shape == matrix.shape[1:], f"Expected shape {matrix.shape[1:]}, got {a.shape}"

            matrix[idx] = a

        return matrix

