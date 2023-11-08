import unittest
from pathlib import Path

from bad import config
from tests.base import BadTestCase
from tests import process1


class TestConfig(BadTestCase):

    def test_config_overload(self):
        normal_value = config.DATA_PATH

        with config.ConfigOverload({
            "DATA_PATH": "/new/path",
        }):
            self.assertEqual(Path("/new/path"), config.DATA_PATH)
            self.assertNotEqual(normal_value, config.DATA_PATH)

            # also check that imported other module's config is overloaded
            self.assertEqual(Path("/new/path"), process1.config.DATA_PATH)

            self.assertEqual("/new/path", config.to_dict(string_values=True)["DATA_PATH"])

        self.assertEqual(normal_value, config.DATA_PATH)
        self.assertEqual(normal_value, process1.config.DATA_PATH)
