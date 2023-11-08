from typing import Optional, Iterable, Tuple, Any, Union, Callable, Dict, List

from bad.util.text import strip_help_text


class ValidationError(Exception):

    def __init__(self, text: str, parameter: Optional["Parameter"] = None):
        super().__init__(text, parameter)


class Parameter:

    type: str = None

    def __init__(
            self,
            name: str,
            default_value: Union[Any, Callable[[], Any]],
            required: bool = True,
            human_name: Optional[str] = None,
            description: Optional[str] = None,
            help: Optional[str] = None,
            visible_js: Optional[str] = None,
            **kwargs,
    ):
        assert "value" not in kwargs, \
            "Please don't specify values for Parameters directly"
        self.kwargs = kwargs
        self.kwargs.update({
            "name": name,
            "human_name": human_name or name,
            "required": bool(required),
            "default_value": default_value,
        })
        if description:
            self.kwargs["description"] = description
        if help:
            self.kwargs["help"] = strip_help_text(help)
        if visible_js:
            self.kwargs["visible_js"] = visible_js

    def __repr__(self):
        kwargs = {
            "name": self.name,
            "default_value": self.default_value,
        }
        extra_kwargs = self.extra_repr_kwargs()
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        kwargs = ', '.join(
            f'{key}: {repr(value)}'
            for key, value in kwargs.items()
        )
        return f"{self.__class__.__name__}({kwargs})"

    def extra_repr_kwargs(self) -> Optional[dict]:
        pass

    @property
    def name(self) -> str:
        return self.kwargs["name"]

    @property
    def default_value(self) -> Any:
        d = self.kwargs["default_value"]
        return d() if callable(d) else d

    @property
    def required(self) -> bool:
        return self.kwargs["required"]

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            **self.kwargs,
            "default_value": self.default_value,
        }

    def validate(self, value):
        """
        Validate the value and maybe convert the type.

        Raise `ValidationError` if something is not right.
        """
        return value


class ParameterSelect(Parameter):
    type = "select"

    class Option:
        def __init__(self, value: Any, name: str):
            self.data = {"value": value, "name": name}

        def __repr__(self):
            return f"{self.data['value']}/{self.data['name']}"

    def __init__(
            self,
            name: str,
            default_value: Union[Any, Callable[[], Any]],
            options: Iterable[Option] = tuple(),
            **kwargs,
    ):
        opt_values = set()
        for opt in options:
            if opt.data["value"] in opt_values:
                raise ValueError(f"Option {name}:{opt} has a duplicate value")
            opt_values.add(opt.data["value"])

        super().__init__(
            name=name,
            default_value=default_value,
            options=[o.data for o in options],
            **kwargs,
        )

    @property
    def options(self) -> List[dict]:
        return self.kwargs["options"]

    def validate(self, value):
        for option in self.kwargs["options"]:
            cmp_value = value
            if type(option["value"]) is not type(value):
                try:
                    cmp_value = type(option["value"])(value)
                except TypeError:
                    continue
            if cmp_value == option["value"]:
                return option["value"]

        values = ', '.join(repr(o["value"]) for o in self.options)
        raise ValidationError(f"Unexpected value '{value}', expect one of {values}", self)


class ParameterInt(Parameter):
    type = "int"

    def __init__(
            self,
            name: str,
            default_value: Union[int, Callable[[], int]] = 0,
            min_value: Optional[int] = None,
            max_value: Optional[int] = None,
            **kwargs,
    ):
        super().__init__(
            name=name,
            default_value=default_value, min_value=min_value, max_value=max_value,
            **kwargs,
        )

    def validate(self, value) -> int:
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Expected integer, got '{value}'", self)

        if self.kwargs["min_value"]:
            value = max(value, self.kwargs["min_value"])
        if self.kwargs["max_value"]:
            value = min(value, self.kwargs["max_value"])

        return value


class ParameterFloat(Parameter):
    type = "float"

    def __init__(
            self,
            name: str,
            default_value: Union[float, Callable[[], float]] = 0.,
            min_value: Optional[float] = None,
            max_value: Optional[float] = None,
            **kwargs,
    ):
        super().__init__(
            name=name,
            default_value=default_value, min_value=min_value, max_value=max_value,
            **kwargs,
        )

    def validate(self, value) -> float:
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Expected float, got '{value}'", self)

        if self.kwargs["min_value"]:
            value = max(value, self.kwargs["min_value"])
        if self.kwargs["max_value"]:
            value = min(value, self.kwargs["max_value"])

        return value


class ParameterString(Parameter):
    type = "string"

    def __init__(
            self,
            name: str,
            default_value: Union[str, Callable[[], str]] = "",
            max_length: Optional[int] = None,
            **kwargs,
    ):
        super().__init__(
            name=name,
            default_value=default_value, max_length=max_length,
            **kwargs,
        )

    def validate(self, value):
        value = str(value)
        if self.kwargs["max_length"]:
            if len(value) >= self.kwargs["max_length"]:
                raise ValidationError(
                    f"Value too long ({len(value)}, expected {self.kwargs['max_length']}",
                    self,
                )

        return value


class ParameterText(ParameterString):
    type = "text"


class ParameterFilepath(ParameterString):
    type = "filepath"


class ParameterFilename(ParameterString):
    type = "filename"


class ParameterBool(Parameter):
    type = "bool"

    def __init__(
            self,
            name: str,
            default_value: Union[bool, Callable[[], bool]] = False,
            **kwargs,
    ):
        super().__init__(
            name=name,
            default_value=default_value,
            **kwargs,
        )

    def validate(self, value) -> bool:
        return bool(value)


class ParameterStringMapping(Parameter):
    type = "string_mapping"

    def __init__(
            self,
            name: str,
            default_value: Optional[Dict[str, str]] = None,
            **kwargs,
    ):
        super().__init__(
            name=name,
            default_value={} if default_value is None else default_value,
            **kwargs,
        )

    def validate(self, value) -> Dict[str, str]:
        return {
            key: str(val)
            for key, val in value.items()
        }
