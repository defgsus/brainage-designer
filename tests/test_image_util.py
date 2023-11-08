import unittest

import numpy as np

from bad.util.image import *
from tests.base import BadTestCase


class TestImageUtil(BadTestCase):

    def test_to_target_shape_2d(self):
        ones = np.ones((2, 3), dtype="int8")
        self.assertEqual(
            [
                [1, 1, 1],
                [1, 1, 1],
            ],
            ones.tolist(),
        )

        self.assertEqual(
            [
                [1, 1],
                [1, 1],
                [0, 0],
            ],
            to_target_shape(ones, (3, 2)).tolist(),
        )

    def test_to_target_shape_3d(self):
        ones = np.ones((1, 2, 3), dtype="int8")
        self.assertEqual(
            [
                [
                    [1, 1, 1],
                    [1, 1, 1],
                ],
            ],
            ones.tolist(),
        )

        self.assertEqual(
            [
                [
                    [1, 1],
                    [1, 1],
                ],
                [
                    [0, 0],
                    [0, 0],
                ],
            ],
            to_target_shape(ones, (2, 2, 2)).tolist(),
        )

        self.assertEqual(
            [
                [
                    [1, 1, 1, 0],
                    [1, 1, 1, 0],
                    [0, 0, 0, 0],
                ],
            ],
            to_target_shape(ones, (1, 3, 4)).tolist(),
        )
