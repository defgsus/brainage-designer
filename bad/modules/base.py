import inspect
import os
from typing import List, Dict, Type, Any, Optional, Generator, Iterable, Union

from bad.logger import Logger
from bad.util.text import strip_help_text
from .params import *
from .form import Form
from .object.base import ModuleObject


registered_modules: Dict[str, Type["Module"]] = dict()


class ModuleGroup:
    # top groups
    SOURCE = "source"
    PROCESS = "process"
    FILTER = "filter"
    # (analysis)
    DATASET = "dataset"
    REDUCTION = "reduction"
    PREDICTION = "prediction"

    # sub-groups
    FILE = "file"
    IMAGE = "image"


class ModuleTag:
    ANALYSIS = "analysis"
    IMAGE_PROCESS = "image_process"
    MULTI_IMAGE_PROCESS = "multi_image_process"


class Module:

    # a unique name for the module
    name: str = None

    # optional help text (markdown)
    help: Optional[str] = None

    # module version, increase whenever the module does something different
    #   to a previous version, even though the parameters are the same
    version: int = 1

    # nested module groups / typically of the `ModuleGroup.<CONSTANTS>`
    group: List[str] = []

    # another filter for modules
    tags: List[str] = []

    # supported in/out types on class level
    input_types: List[str] = []
    output_types: List[str] = []

    # class level parameter definition
    parameters: List[Parameter] = []

    def __init_subclass__(cls, **kwargs):
        if not cls.__name__.endswith("Base"):
            for key in ["name", "group"]:
                if not getattr(cls, key):
                    raise AssertionError(f"Must set {cls.__name__}.{key} property")

            for key in ["input_types", "output_types"]:
                if not isinstance(getattr(cls, key), (tuple, list)):
                    raise TypeError(f"{cls.__name__}.{key} must be a list or tuple of strings")

            if cls.name in registered_modules:
                registered_file = inspect.getabsfile(registered_modules[cls.name]).strip(os.path.sep)
                new_file = inspect.getabsfile(cls).strip(os.path.sep)
                if registered_file != new_file:
                    raise AssertionError(
                        f"Duplicate module name '{cls.name}' in class {cls.__name__}."
                        f" Got {cls} but {registered_modules[cls.name]} is already registered"
                    )

            registered_modules[cls.name] = cls

    def __init__(self):
        """
        Don't construct these yourself. Use the `ModuleFactory`.
        """
        from bad.process import ProcessBase
        self.uuid = None
        self._parameter_values = dict()
        self._parameter_default_values = dict()
        self._process: Optional[ProcessBase] = None
        self._log = None

    def __repr__(self):
        return f"{self.__class__.__name__}({'.'.join(self.group)}/{self.name}/{self.uuid})"

    @property
    def log(self) -> Logger:
        if not self._log:
            self._log = Logger(f"{self.__class__.__name__}/{self.uuid}")
        return self._log

    @property
    def parameter_values(self) -> Dict[str, Any]:
        """
        Immutable parameter values
        """
        return self._parameter_values

    @property
    def process(self):
        """
        Access to the Process that is currently using the module
        """
        return self._process

    @property
    def process_item(self):
        if self._process:
            return self._process.process_item

    def get_parameter_value(self, name: str) -> Any:
        """
        Retrieve a parameter value.

        Either the default_value or the parameter store in database for this module
        """
        if not self._parameter_default_values:
            self._parameter_default_values = self.get_form().get_default_values()

        return self.parameter_values.get(name, self._parameter_default_values.get(name))

    def get_form(self) -> Form:
        """
        Construct a form description for the module
        :return:
        """
        form = Form(f"{self.name}_{self.uuid}" if self.uuid else self.name)
        form.set_parameters(self.parameters)
        return form

    def prepare(self):
        """
        Called on start of module processing
        """
        pass

    @classmethod
    def class_to_dict(cls) -> dict:
        return {
            "name": cls.name,
            "group": cls.group,
            "tags": cls.tags,
            "version": cls.version,
            "help": strip_help_text(cls.help) if cls.help else None,
        }

    def to_dict(self) -> dict:
        form = self.get_form()
        return {
            **self.class_to_dict(),
            "uuid": self.uuid,
            "parameter_values": {
                **form.get_default_values(),
                **self._parameter_values,
            },
            "form": form.to_dict(),
        }

    def action_dict(
            self,
            action_name: Optional[str] = None,
            **data_kwargs,
    ) -> dict:
        module_dict = self.to_dict()
        module_dict.pop("group", None)
        module_dict.pop("form", None)
        return {
            "name": action_name or self.name,
            "module": module_dict,
            "data": data_kwargs,
        }


class SourceModuleBase(Module):
    group = [*Module.group, ModuleGroup.SOURCE]

    parameters = [
        ParameterString(
            name="module_object_sub_path", default_value="",
            description="Prepend all filenames with this Sub-directory",
            required=False,
        ),
    ]

    def get_object_count(self) -> int:
        raise NotImplementedError

    def iter_objects(
            self,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
    ) -> Generator[Any, None, None]:
        raise NotImplementedError


class FilterModuleBase(Module):
    group = [*Module.group, ModuleGroup.FILTER]

    def filter_objects(
            self,
            objects: Iterable[ModuleObject],
            stub: bool = False,
    ) -> Generator[ModuleObject, None, None]:
        raise NotImplementedError


class ProcessModuleBase(Module):
    group = [*Module.group, ModuleGroup.PROCESS]

    parameters = [
        ParameterBool(
            name="module_store_result", default_value=False,
            description="Store the result of this processing step.",
            help="""
            If selected each processed object is stored to disk. 
            
            The final module in a pipeline will store it's results in any case.
            """
        ),
        ParameterString(
            name="module_result_path", default_value="",
            required=False,
            description="Sub-directory where the results are stored.",
            help="""
            The processed objects of this module will be stored in:
            
                <pipeline target path> / <result path> / <object sub-path> / <object filename>
                
            Leave the result path empty to assign automatically. 
            In this case the path will be either equal to the module's name
            or named `final/` for the last module in the pipeline. 
            """
        )
    ]

    def process_objects(
            self,
            objects: Iterable[ModuleObject],
            stub: bool = False,
    ) -> Generator[ModuleObject, None, None]:
        raise NotImplementedError


ModuleLike = Union[Module, SourceModuleBase, FilterModuleBase, ProcessModuleBase]
