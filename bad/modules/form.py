from typing import Iterable, List, Optional, Dict, Any

from .params import Parameter, ValidationError


class Form:

    def __init__(
            self,
            id: str,
            parameters: Optional[Iterable[Parameter]] = None,
    ):
        self.id = id
        self.parameters: List[Parameter] = []
        if parameters:
            self.set_parameters(parameters)

    def set_parameters(self, parameters: Iterable[Parameter]):
        self.parameters = list(parameters)

        name_set = set()
        for param in self.parameters:
            if param.name in name_set:
                raise AssertionError(f"Duplicate name '{param.name}' in {param}")
            name_set.add(param.name)

    def to_dict(self):
        return {
            "type": "form",
            "id": self.id,
            "parameters": [
                param.to_dict()
                for param in self.parameters
            ],
        }

    def get_default_values(self) -> Dict[str, Any]:
        """
        Return a dict of all default values
        """
        mapping = dict()
        for p in self.parameters:
            mapping[p.name] = p.default_value
        return mapping

    def get_default_value(self, name: str) -> Optional[Any]:
        """
        Return a default value or None
        """
        for p in self.parameters:
            if p.name == name:
                return p.default_value

    def get_values(self, values: Optional[dict] = None) -> Dict[str, Any]:
        """
        Return a dict of all parameter values,
        either from `values` parameter or for default values
        """
        mapping = self.get_default_values()
        for key in mapping:
            if values and key in values:
                mapping[key] = values[key]
        return mapping

    def get_parameter(self, name: str) -> Optional[Parameter]:
        for p in self.parameters:
            if p.name == name:
                return p

    def validate(self, values: Dict[str, Any], require_known: bool = False) -> Dict[str, Any]:
        ret_values = {}
        for name, value in values.items():
            param = self.get_parameter(name)
            if param:
                value = param.validate(value)
            else:
                if require_known:
                    raise ValidationError(f"Unknown parameter '{name}'")

            ret_values[name] = value

        return ret_values
