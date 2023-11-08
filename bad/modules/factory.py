import uuid
from typing import Optional

from .base import registered_modules, Module, ModuleLike


class ModuleFactory:

    @classmethod
    def new_module(
            cls,
            name: str,
            parameters: Optional[dict] = None,
            prepare: bool = False,
    ) -> ModuleLike:
        if name not in registered_modules:
            raise ValueError(f"No module named '{name}'")

        module = registered_modules[name]()
        module.uuid = f"mod-{uuid.uuid4()}"
        if parameters:
            form = module.get_form()
            valid_parameters = form.validate(parameters, require_known=True)
            module._parameter_values.update(valid_parameters)

        if prepare:
            module.prepare()
        return module

    @classmethod
    def from_dict(self, data: dict, process: Optional["ProcessBase"] = None) -> ModuleLike:
        if not data.get("name"):
            raise ValueError(f"No name in module dict")

        name = data["name"]
        if name not in registered_modules:
            raise ValueError(f"No registered module '{name}'")

        module = registered_modules[name]()
        module.uuid = data.get("uuid") or f"mod-{uuid.uuid4()}"
        module._parameter_values = data.get("parameter_values") or {}
        module._process = process

        return module
