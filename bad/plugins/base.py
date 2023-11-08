from typing import Optional, Iterable, Mapping, Any, Sequence, Union, Type, List

import pymongo.database

from bad import logger
from bad.process import ProcessItem, ProcessDb
from bad.modules import Module, registered_modules, ModuleFactory

registered_plugins = dict()


class PluginBase:

    # a unique name for the plugin
    name: str = None

    # list of supported modules for this plugin
    # either a Module class, a Module.name
    #   or "__all__" to add all modules.
    # Later read the classes from `cls.available_module_classes`
    available_modules: Sequence[Union[str, Type[Module]]] = []

    # filter modules by `tags` if not empty
    available_module_tags: Sequence[Union[str, Type[Module]]] = []

    def __init_subclass__(cls, **kwargs):
        if not cls.name:
            raise AssertionError(f"Must set {cls.__name__}.name property")
        if cls.name in registered_plugins:
            raise AssertionError(f"Duplicate plugin name '{cls.name}' in class {cls.__name__}")

        registered_plugins[cls.name] = cls

    def __init__(self, server: "Server"):
        self.server = server
        self.log = logger.Logger(self.name)

    def terminate(self):
        pass

    def database(self) -> pymongo.database.Database:
        return self.server.database()

    def get_handlers(self) -> Optional[Iterable]:
        pass

    def request_process(
            self,
            name: str,
            kwargs: Optional[Mapping[str, Any]] = None,
            source_uuid: Optional[str] = None,
    ) -> ProcessItem:
        return ProcessDb().request_process(name, kwargs, source_uuid)

    def get_latest_process_item(self, source_uuid: str) -> Optional[ProcessItem]:
        db = ProcessDb()
        coll = db.collection()
        process_data = coll.find_one(
            filter={"source_uuid": source_uuid},
            sort=[("date_created", pymongo.DESCENDING)],
        )
        if process_data:
            return db.get_process(process_data["uuid"])

    def get_latest_process_uuid(self, source_uuid: str) -> Optional[str]:
        db = ProcessDb()
        coll = db.collection()
        process_data = coll.find_one(
            filter={"source_uuid": source_uuid},
            sort=[("date_created", pymongo.DESCENDING)],
            projection=["uuid"]
        )
        return None if not process_data else process_data["uuid"]

    def get_latest_process_data(self, source_uuid: str) -> Optional[dict]:
        db = ProcessDb()
        coll = db.collection()
        process_data = coll.find_one(
            filter={"source_uuid": source_uuid},
            sort=[("date_created", pymongo.DESCENDING)],
        )
        if not process_data:
            return

        coll = db.collection_events()
        events = coll.find({"process_uuid": process_data["uuid"]}).sort("date_created", pymongo.ASCENDING)

        object_count = db.get_objects_count(process_data["uuid"])

        return {
            **process_data,
            "events": list(events),
            "object_count": object_count,
        }

    @classmethod
    def class_to_dict(cls) -> dict:
        return {
            "plugin_name": cls.name,
            "available_modules": [
                m.class_to_dict()
                for m in cls.available_module_classes()
            ],
        }

    @classmethod
    def available_module_classes(cls) -> List[Type[Module]]:
        modules = set()
        for mod in cls.available_modules:
            try:
                if issubclass(mod, Module):
                    modules.add(mod)
                    continue
            except TypeError:
                pass

            if isinstance(mod, str):
                if mod == "__all__":
                    for mod_class in registered_modules.values():
                        modules.add(mod_class)

                else:
                    if mod not in registered_modules:
                        raise ValueError(
                            f"Unknown module '{mod}' in {cls.__name__}.available_modules"
                        )
                    modules.add(registered_modules[mod])
            else:
                raise TypeError(f"Invalid type '{type(mod)}' in {cls.__name__}.available_modules")

        if cls.available_module_tags:
            modules = filter(
                lambda m: any(t in m.tags for t in cls.available_module_tags),
                modules,
            )

        return sorted(modules, key=lambda m: m.name)

    def handle_websocket_message(self, client_id: str, name: str, data: dict) -> bool:
        """
        Override to handle every websocket message from the browser.

        :param client_id: id of the browser session
        :param name: name of the message
        :param data: json compatible object
        :return:
        """
        return False

    def update_module_dict(self, module_dict: dict) -> dict:
        """
        Update a module dict (e.g. from database) to match the current module class
        :param module: dict
        :return: new dict
        """
        module = ModuleFactory.from_dict(module_dict)
        form = module.get_form()
        return {
            **module.to_dict(),
            "parameter_values": form.get_values(module_dict.get("parameter_values")),
        }
