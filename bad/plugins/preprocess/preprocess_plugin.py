import datetime
import uuid as uuidlib
from copy import deepcopy
from typing import Optional, Iterable, Mapping, Any

from bad.plugins import PluginBase
from bad.server.handlers import JsonBaseHandler, DbRestHandler
from bad.modules import *
from .preprocess_process import PreprocessingProcess

# register plugin's modules
from . import modules


class PreprocessPlugin(PluginBase):
    name = "preprocess"
    available_modules = [
        "__all__",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/api/preprocess/([a-z0-9\-]*)/start/?", PreprocessStartHandler),
            (r"/api/preprocess/([a-z0-9\-]*)/stop/?", PreprocessStopHandler),
            (r"/api/preprocess/([a-z0-9\-]*)/copy/?", PreprocessCopyHandler),
            (r"/api/preprocess/([a-z0-9\-]*)/?", PreprocessRestHandler),
        ]

    def get_config_form(self) -> Form:
        form = Form("preprocessing")
        form.set_parameters([
            ParameterString(
                name="name", default_value="preprocessing pipeline name",
            ),
            ParameterText(
                name="description", default_value="",
                required=False,
            ),
            ParameterInt(
                name="num_processes", default_value=1,
                description="The number of parallel processes when running the pipeline",
                help="""
                Selects the number of parallel processes to run the pipeline.
                Each process runs its own set of source file through the pipeline.
                
                **Warning**: Each additional process adds more memory and computation
                requirements. It is generally not helpful to request more processes
                than available CPU cores or hyper-threads. Also, for heavy modules like
                the *CAT12 Preprocessing* the memory requirements for each process are
                several Gigabytes.
                """
            ),
            ParameterFilepath(
                name="target_path", default_value="/",
                description="The base directory to store all results",
                help="""
                All processed files will (eventually) be written below this directory.
                """
            ),
            ParameterSelect(
                name="skip_policy", default_value=ModuleGraph.SkipPolicy.UNCHANGED,
                description="Skip processing of source files",
                options=[
                    ParameterSelect.Option(ModuleGraph.SkipPolicy.NEVER, "never"),
                    ParameterSelect.Option(ModuleGraph.SkipPolicy.EXISTS, "targets exist"),
                    ParameterSelect.Option(ModuleGraph.SkipPolicy.UNCHANGED, "exist & unchanged"),
                ],
                help="""
                Each source file (e.g. an image) can generate multiple target files through the
                processing pipeline. With this setting, needless re-processing of source files 
                can be avoided.
                
                - **never**: no skipping, always re-process all source files
                - **targets exist**: If all target files exist for a source, it is skipped
                - **exist & unchanged**: If all target files exist and neither the source
                  or target files modification date nor the involved processing modules 
                  parameters have changed, the source is skipped.  
                """
            ),
        ])
        return form


class PreprocessRestHandler(DbRestHandler):

    collection_name = "preprocess"
    uuid_prefix = "pp"
    columns = [
        {"name": "date_created", "type": "datetime"},
        {"name": "uuid", "type": "uuid"},
        {"name": "name", "type": "str"},
        {"name": "description", "type": "text"},
    ]
    default_sort = "-date_created"

    def after_db_read(self, obj: dict) -> None:
        # add stuff to frontend response
        obj.update(self.plugin.class_to_dict())
        form: Form = self.plugin.get_config_form()

        obj["config_form"] = form.to_dict()
        for key, value in form.get_default_values().items():
            if key not in obj:
                obj[key] = value
        latest_process_data = self.plugin.get_latest_process_data(obj["uuid"])
        if latest_process_data:
            obj["latest_process_data"] = latest_process_data

        # update stored modules from current module classes
        if obj.get("modules"):
            for idx, module_dict in enumerate(obj["modules"]):
                obj["modules"][idx] = self.plugin.update_module_dict(module_dict)

    def before_db_insert(self, obj: dict) -> None:
        # remove stuff added to frontend response
        obj.pop("available_modules", None)
        obj.pop("latest_process_data", None)
        obj.pop("config_form", None)

        if "modules" in obj:
            obj["modules"] = obj.get("modules") or []
            for idx, module_dict in enumerate(obj["modules"]):
                # reconstruct from class (don't fully trust the frontend)
                module = ModuleFactory.from_dict(module_dict)
                obj["modules"][idx] = module.to_dict()


class PreprocessStartHandler(JsonBaseHandler):

    def post(self, uuid):
        coll = self.plugin.database()[PreprocessRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})
        if not document:
            self.set_status(404)
            self.write({"detail": "Not found"})
            return

        plugin_state = dict(document)

        # add parameter default values
        config_form: Form = self.plugin.get_config_form()
        plugin_state.update(config_form.get_values(plugin_state))

        proc = self.plugin.request_process(
            name=PreprocessingProcess.name,
            source_uuid=uuid,
            kwargs={
                # store snapshot of the plugin and all of it's modules
                "plugin": plugin_state
            },
        )
        self.write({"process_uuid": proc.uuid})


class PreprocessStopHandler(JsonBaseHandler):

    def post(self, uuid):
        coll = self.plugin.database()[PreprocessRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})
        if not document:
            self.set_status(404)
            self.write({"detail": "Not found"})
            return

        proc = self.plugin.get_latest_process_item(uuid)
        if proc:
            proc.kill()

        self.write({"process_uuid": proc.uuid})


class PreprocessCopyHandler(JsonBaseHandler):

    def post(self, uuid):
        coll = self.plugin.database()[PreprocessRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})
        if not document:
            self.set_status(404)
            self.write({"detail": "Not found"})
            return

        document = dict(document)
        document.pop("_id", None)
        document["uuid"] = f"pp-{uuidlib.uuid4()}"
        document["date_created"] = datetime.datetime.utcnow().isoformat()
        document["name"] = f'{document["name"]} (copy)'

        coll.insert_one(document)

        self.write(document)
