import datetime
import json
import math
import os.path

import time
import uuid as uuidlib
from functools import partial
from copy import deepcopy
from typing import Optional, Iterable, Mapping, Any

from bad.plugins import PluginBase
from bad.server.handlers import JsonBaseHandler, DbRestHandler
from bad.parallel import ThreadWorker
from bad.modules import *

from .analysis_process import AnalysisProcess
from .handlers.source_preview import AnalysisSourcePreviewHandler
from .reduction import AnalysisReduction
from .analysis import Analysis


class AnalysisPlugin(PluginBase):
    name = "analysis"
    available_modules = [
        "__all__",
    ]
    available_module_tags = [ModuleTag.ANALYSIS, ModuleTag.IMAGE_PROCESS]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker = ThreadWorker(1)
        self.worker.start()

    def terminate(self):
        self.worker.stop()

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/api/analysis/([a-z0-9\-]*)/start/", AnalysisStartHandler),
            (r"/api/analysis/([a-z0-9\-]*)/stop/", AnalysisStopHandler),
            (r"/api/analysis/([a-z0-9\-]*)/copy/", AnalysisCopyHandler),
            (r"/api/analysis/([a-z0-9\-]*)/result/", AnalysisResultHandler),
            (r"/api/analysis/([a-z0-9\-]*)/source-preview/", AnalysisSourcePreviewHandler),
            (r"/api/analysis/([a-z0-9\-]*)/?", AnalysisRestHandler),
            (r"/api/analysis/results/([a-z0-9\-]*)/?", AnalysisResultsHandler),
        ]

    def get_config_form(self) -> Form:
        form = Form("analysis")
        form.set_parameters([
            ParameterString(
                name="name", default_value="analysis",
            ),
            ParameterText(
                name="description", default_value="",
                required=False,
            ),
        ])
        return form

    def on_websocket_reduction_preview(self, client_id: str, uuid: str, data: dict):
        self.worker.put(partial(self._get_reduction_preview, client_id, uuid))

    def _get_reduction_preview(self, client_id: str, uuid: str):
        coll = self.database()[AnalysisRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})

        if not document or not document.get("modules"):
            result = {"error": f"not found"}
        else:
            modules = [
                ModuleFactory.new_module(
                    name=mod["name"],
                    parameters=mod["parameter_values"],
                )
                for mod in document["modules"]
            ]
            for m in modules:
                m.prepare()

            reduction = AnalysisReduction(
                modules=modules,
                separation_values=document.get("separation_values") or None,
                reduction_values=document.get("reduction_values") or None,
            )
            reduction.init()

            train_files, validation_files = reduction.split_files_to_train_and_validation()

            result = {
                "files": reduction.files,
                "attribute_names": reduction.attribute_names,
                "counts": reduction.get_file_counts(),
                "sets": {
                    "training": train_files,
                    "validation": validation_files,
                },
                "output_size": reduction.get_output_size()
            }
            result["preview_str"] = " | ".join(
                f"{key}: {len(result['sets'][key])} files" + (
                  f" (reduced shape: {len(result['sets'][key])} x {result['output_size']})" if result["output_size"] else ""
                )
                for key in result["sets"]
            )

        result["uuid"] = uuid
        self.server.send_message(f"analysis:{uuid}:reduction_preview", result, client=client_id)


class AnalysisRestHandler(DbRestHandler):

    collection_name = "analysis"
    uuid_prefix = "ap"
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

        # -- config form ---
        form: Form = self.plugin.get_config_form()
        obj["config_form"] = form.to_dict()
        for key, value in form.get_default_values().items():
            if key not in obj:
                obj[key] = value

        # --- separation form ---
        form = AnalysisReduction.get_separation_form()
        obj["separation_form"] = form.to_dict()
        if "separation_values" not in obj:
            obj["separation_values"] = {}
        for key, value in form.get_default_values().items():
            if key not in obj["separation_values"]:
                obj["separation_values"][key] = value

        # --- reduction form ---
        form = AnalysisReduction.get_reduction_form()
        obj["reduction_form"] = form.to_dict()
        if "reduction_values" not in obj:
            obj["reduction_values"] = {}
        for key, value in form.get_default_values().items():
            if key not in obj["reduction_values"]:
                obj["reduction_values"][key] = value

        # --- analysis form ---
        form = Analysis.get_form()
        obj["analysis_form"] = form.to_dict()
        if "analysis_values" not in obj:
            obj["analysis_values"] = {}
        for key, value in form.get_default_values().items():
            if key not in obj["analysis_values"]:
                obj["analysis_values"][key] = value

        latest_process_data = self.plugin.get_latest_process_data(obj["uuid"])
        if latest_process_data:
            obj["latest_process_data"] = latest_process_data

        # --- reconstruct modules and parameters ---

        REMOVE_PARAMETERS = ("module_store_result", "module_result_path")

        def _remove_parameters(module: dict) -> dict:
            module["form"]["parameters"] = [
                p for p in module["form"]["parameters"]
                if p["name"] not in REMOVE_PARAMETERS
            ]
            for key in REMOVE_PARAMETERS:
                module["parameter_values"].pop(key, None)
            return module

        if obj.get("modules"):
            for idx, module_dict in enumerate(obj["modules"]):
                obj["modules"][idx] = _remove_parameters(self.plugin.update_module_dict(module_dict))

    def before_db_insert(self, obj: dict) -> None:
        # remove stuff added to frontend response
        for key in (
            "available_modules",
            "latest_process_data",
            "config_form",
            "separation_form",
            "reduction_form",
            "analysis_form",
        ):
            obj.pop(key, None)

        if "modules" in obj:
            obj["modules"] = obj.get("modules") or []
            for idx, module_dict in enumerate(obj["modules"]):
                # reconstruct from class (don't fully trust the frontend)
                module = ModuleFactory.from_dict(module_dict)
                obj["modules"][idx] = module.to_dict()

        # if "separation_values" in obj:


class AnalysisCopyHandler(JsonBaseHandler):

    def post(self, uuid):
        coll = self.plugin.database()[AnalysisRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})
        if not document:
            self.set_status(404)
            self.write({"detail": "Not found"})
            return

        document = dict(document)
        document.pop("_id", None)
        document["uuid"] = f"ap-{uuidlib.uuid4()}"
        document["date_created"] = datetime.datetime.utcnow().isoformat()
        document["name"] = f'{document["name"]} (copy)'

        coll.insert_one(document)

        self.write(document)


class AnalysisStartHandler(JsonBaseHandler):

    def post(self, uuid):
        coll = self.plugin.database()[AnalysisRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})
        if not document:
            self.set_status(404)
            self.write({"detail": "Not found"})
            return

        plugin_state = dict(document)
        plugin_state.pop("_id", None)

        # add parameter default values
        config_form: Form = self.plugin.get_config_form()
        plugin_state.update(config_form.get_values(plugin_state))
        #plugin_state["separation_values"].update(AnalysisReduction.get_separation_form().get_values(plugin_state["separation_values"]))

        proc = self.plugin.request_process(
            name=AnalysisProcess.name,
            source_uuid=uuid,
            kwargs={
                # store snapshot of the plugin and all of it's modules
                "plugin": plugin_state
            },
        )
        self.write({"process_uuid": proc.uuid})


class AnalysisStopHandler(JsonBaseHandler):

    def post(self, uuid):
        coll = self.plugin.database()[AnalysisRestHandler.collection_name]
        document = coll.find_one({"uuid": uuid})
        if not document:
            self.set_status(404)
            self.write({"detail": "Not found"})
            return

        proc = self.plugin.get_latest_process_item(uuid)
        if proc:
            proc.kill()

        self.write({"process_uuid": proc.uuid})


class AnalysisResultsHandler(DbRestHandler):

    collection_name = "analysis_results"
    uuid_prefix = "ar"
    columns = [
        {"name": "timestamp", "type": "datetime"},
        {"name": "uuid", "type": "uuid"},
        {"name": "analysis_uuid", "type": "uuid"},
        {"name": "process_uuid", "type": "uuid"},
        {"name": "run_index", "type": "int"},
        {"name": "num_training_samples", "type": "int"},
        {"name": "num_validation_samples", "type": "int"},
        {"name": "feature_size", "type": "int"},
        {"name": "reduction_time", "type": "float"},
        {"name": "training_time", "type": "float"},
        {"name": "validation_loss_l1", "type": "float"},
        {"name": "validation_loss_l2", "type": "float"},
        {"name": "validation_value_average", "type": "float"},
        {"name": "validation_value_std", "type": "float"},
        {"name": "predicted_value_average", "type": "float"},
        {"name": "predicted_value_std", "type": "float"},
    ]
    default_sort = "-timestamp"



class AnalysisResultHandler(JsonBaseHandler):

    def get(self, uuid):
        process_uuid = self.get_query_argument("process_uuid", None)
        if not process_uuid:
            process_uuid = self.plugin.get_latest_process_uuid(uuid)

        if not process_uuid:
            self.set_status(404)
            return

        search_query = {
            "analysis_uuid": uuid,
            "process_uuid": process_uuid,
        }

        coll = self.plugin.database().get_collection(AnalysisResultsHandler.collection_name)
        cursor = coll.find(search_query)

        average = Analysis.build_average_result(cursor)

        self.write({
            "average": average
        })
