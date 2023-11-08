from pathlib import Path
from typing import Generator, Iterable

from bad import config
from ..base import FilterModuleBase
from ..object.base import ModuleObject, ModuleObjectType
from ..params import *


class FilterCountModule(FilterModuleBase):
    name = "filter_count"
    input_types = ModuleObjectType.all
    output_types = ModuleObjectType.all

    parameters = [
        ParameterInt(
            name="max_count",
            default_value=0,
            description="Limit the number of subjects if not zero."
                        " TODO: Currently the number is multiplied by the number of parallel processes!",
        ),
        *FilterModuleBase.parameters,
    ]

    def filter_objects(
            self,
            objects: Iterable[ModuleObject],
            stub: bool = False,
    ) -> Generator[ModuleObject, None, None]:
        max_count = self.get_parameter_value("max_count")
        for i, obj in enumerate(objects):
            if max_count and i >= max_count:
                break
            yield obj
