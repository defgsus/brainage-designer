import argparse
import inspect
import os
import json
from typing import Mapping, Any, Optional, List, Dict, Iterable

from bad import logger
from bad.db import DatabaseMixin
from bad.modules import ModuleFactory, Module, ModuleGraph

registered_processes = dict()


class ProcessBase(DatabaseMixin):
    """
    Base class for processes that run outside the api-server.

    Layout your process file like this:

        from bad.process import ProcessBase

        class MyProcess(ProcessBase):
            name = "my-process"

            def run(self):
                self.kwargs  # contains caller parameters
                self.store_event("info", "i can write to database")

                # create all modules and set parameters from database
                module_graph = self.create_module_graph()

        if __name__ == "__main__":
            MyProcess.run_from_commandline()

    """
    name: str = None

    def __init_subclass__(cls, **kwargs):
        assert cls.name, f"Must {cls.__name__}.name property"
        if cls.name in registered_processes:
            registered_file = inspect.getabsfile(registered_processes[cls.name]).strip(os.path.sep)
            new_file = inspect.getabsfile(cls).strip(os.path.sep)
            if registered_file != new_file:
                raise AssertionError(
                    f"Duplicate process name '{cls.name}'"
                    f", class {registered_processes[cls.name]} is already registered"
                    f", can't register {cls}"
                    f"\nregistered file: {registered_file}"
                    f"\nnew file:        {new_file}"
                )

        registered_processes[cls.name] = cls

    def __init__(self, uuid: str, do_raise: bool = False):
        from bad.process import ProcessDb
        super().__init__()
        self.uuid = uuid
        self.do_raise = do_raise
        self.log = logger.Logger(f"{self.name}/{self.uuid}")
        self.process_item = ProcessDb().get_process(self.uuid)
        assert self.process_item, f"running {self.__class__.__name__} on non-existing process '{self.uuid}'"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.uuid)})"

    def __getstate__(self):
        return {
            "uuid": self.uuid,
            "do_raise": self.do_raise,
        }

    def __setstate__(self, state):
        from bad.process import ProcessDb
        self.uuid = state["uuid"]
        self.do_raise = state["do_raise"]

        self.log = logger.Logger(f"{self.name}/{self.uuid}")
        self.process_item = ProcessDb().get_process(self.uuid)
        assert self.process_item, f"running {self.__class__.__name__} on non-existing process '{self.uuid}'"

    @property
    def kwargs(self) -> Mapping[str, Any]:
        return self.process_item.kwargs

    def create_module_graph(self, **kwargs) -> ModuleGraph:
        """Only suitable for processing stage!"""
        kwargs.setdefault("modules", [
            ModuleFactory.from_dict(module_dict, process=self)
            for module_dict in self.process_item.kwargs["plugin"]["modules"]
        ])
        kwargs.setdefault("target_path", self.process_item.kwargs["plugin"]["target_path"])
        if "skip_policy" in self.process_item.kwargs["plugin"]:
            kwargs.setdefault("skip_policy", self.process_item.kwargs["plugin"]["skip_policy"])
        return ModuleGraph(**kwargs)

    def store_event(
            self,
            type: str,
            text: Optional[str] = None,
            data: Optional[Mapping[str, Any]] = None,
    ):
        self.process_item.store_event(type=type, text=text, data=data)

    @classmethod
    def create_from_commandline(cls) -> "ProcessBase":
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "uuid",
            type=str,
            help="The process uuid",
        )
        parser.add_argument(
            "--raise", type=bool, nargs="?", default=False, const=True,
            help="Let exceptions propagate outside",
        )

        args = parser.parse_args()

        process = cls(args.uuid, do_raise=getattr(args, "raise"))
        return process

    @classmethod
    def run_from_commandline(cls):
        process = cls.create_from_commandline()
        process.run_and_catch()

    def run_and_catch(self):
        try:
            self.run()

        except Exception as e:
            self.log.error(f"{type(e).__name__}: {e}")
            self.process_item.store_exception_event(e)
            if not self.do_raise:
                exit(1)
            else:
                raise

    def run(self):
        raise NotImplementedError
