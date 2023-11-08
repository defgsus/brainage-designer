import datetime
import uuid
from typing import Optional, Iterable

from bad.plugins import PluginBase
from bad.server.handlers import JsonBaseHandler, DbRestHandler


class ProcessPlugin(PluginBase):
    name = "process"

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/api/process/event/([a-z0-9\-]*)/?", EventRestHandler),
            (r"/api/process/object/module/?", ObjectsByModuleRestHandler),
            (r"/api/process/object/([a-z0-9\-]*)/?", ObjectRestHandler),
            (r"/api/process/([a-z0-9\-]*)/?", ProcessRestHandler),
        ]


class ProcessRestHandler(DbRestHandler):

    collection_name = "process"
    uuid_prefix = "p"
    columns = [
        {"name": "date_created", "type": "datetime"},
        {"name": "uuid", "type": "uuid"},
        {"name": "name", "type": "str"},
        {"name": "type", "type": "state"},
        {"name": "status", "type": "state"},
        {"name": "pid", "type": "str"},
        {"name": "source_uuid", "type": "uuid"},
    ]
    default_sort = "-date_created"


class EventRestHandler(DbRestHandler):

    collection_name = "process_events"
    uuid_prefix = "pe"
    columns = [
        {"name": "timestamp", "type": "datetime"},
        {"name": "uuid", "type": "uuid"},
        {"name": "process_uuid", "type": "uuid"},
        {"name": "source_uuid", "type": "uuid"},
        {"name": "type", "type": "state"},
        {"name": "text", "type": "text"},
        {"name": "data", "type": "data"},
    ]
    default_sort = "-timestamp"


class ObjectsByModuleRestHandler(JsonBaseHandler):

    def get(self):
        process_uuid = self.get_query_argument("process_uuid")
        module_uuid = self.get_query_argument("module_uuid")
        source = self.get_query_argument("source")

        coll = self.server.database()["process_objects"]
        pipeline = [
            {"$match": {"process_uuid": process_uuid, f"{source}_module": module_uuid}},
            {"$group": {"_id": f"${source}_filename"}}
        ]
        aggregation = coll.aggregate(pipeline)
        self.write({
            "result": sorted(o["_id"] for o in aggregation)
        })


class ObjectRestHandler(DbRestHandler):

    collection_name = "process_objects"
    uuid_prefix = "o"
    columns = [
        {"name": "timestamp", "type": "datetime"},
        {"name": "uuid", "type": "uuid"},
        {"name": "process_uuid", "type": "uuid"},
        {"name": "source_uuid", "type": "uuid"},
        {"name": "type", "type": "state"},
        {"name": "skipped", "type": "bool"},
        {"name": "source_module", "type": "uuid"},
        {"name": "source_filename", "type": "filename"},
        {"name": "target_module", "type": "uuid"},
        {"name": "target_filename", "type": "filename"},
        {"name": "data", "type": "data"},
    ]
    default_sort = "-timestamp"
