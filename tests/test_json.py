import unittest

from bad.server.serializer import to_json


class TestJson(unittest.TestCase):

    def test_no_nan(self):
        self.assertEqual(
            '{"a":23,"b":null}',
            to_json({"a": 23, "b": float("NaN")})
        )
        self.assertEqual(
            '{"a":[{"b":null}]}',
            to_json({"a": [{"b": float("NaN")}]})
        )
