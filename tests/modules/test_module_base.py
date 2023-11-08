import unittest
import json
from typing import Iterable, Generator

from bad import config
from bad.modules import *
from tests.base import BadTestCase
# register test modules
from tests.modules import testmodules


class TestModuleBase(BadTestCase):

    def test_factory(self):
        ModuleFactory.new_module("image_resample")
        ModuleFactory.new_module("test_multi_image")
