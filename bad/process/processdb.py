import dataclasses
import datetime
import os
import signal
import uuid
import traceback
from typing import Mapping, Any, Optional, Union, Sequence

import pymongo
from pymongo.database import Collection, List

from bad.db import DatabaseMixin
from bad import logger
from bad.modules import ModuleObject


class ProcessStatus:
    STUB = "stub"
    REQUESTED = "requested"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    KILLED = "killed"


class EventType:
    INFO = "info"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    KILLED = "killed"
    ERROR = "error"
    EXCEPTION = "exception"
    GRAPH_RESULT = "graph_result"


@dataclasses.dataclass
class Progress:
    title: str = ""
    data: Optional[dict] = None

    def to_dict(self):
        return vars(self)


class ProcessItem:
    """
    A link between a running Process and the database
    """
    def __init__(
            self,
            db: "ProcessDb",
            name: str,
            uuid: str,
            kwargs: Mapping[str, Any],
            source_uuid: Optional[str] = None,
    ):
        self.db = db
        now = datetime.datetime.utcnow().isoformat()
        self._data = {
            "name": name,
            "uuid": uuid,
            "kwargs": kwargs,
            "status": ProcessStatus.STUB,
            "source_uuid": source_uuid,
            "date_created": now,
            "pid": None,
            "progress": None,
            "source_object_count": None,
        }
        self.log = logger.Logger(self.uuid)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"uuid={repr(self.uuid)}, target={repr(self.name)}, status={repr(self.status)})"
        )

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def uuid(self) -> str:
        return self._data["uuid"]

    @property
    def kwargs(self) -> Mapping[str, Any]:
        return self._data["kwargs"]

    @property
    def status(self) -> str:
        return self._data["status"]

    @property
    def source_uuid(self) -> str:
        return self._data["source_uuid"]

    @property
    def date_created(self) -> str:
        return self._data["date_created"]

    @property
    def pid(self) -> Optional[int]:
        return self._data["pid"]

    def update_from_db(self) -> "ProcessItem":
        self.db._read_item(self)
        return self

    def store_status(self, status: str, pid: Optional[int] = None):
        self._data["status"] = status
        update_only = ["status"]
        if pid is not None:
            self._data["pid"] = pid
            update_only.append("pid")
        self.db._store_item(self, update_only=update_only)

    def store_source_object_count(self, count_map: dict):
        self._data["source_object_count"] = count_map
        self.db._store_item(self, update_only="source_object_count")

    def store_progress(self, progress: Progress):
        self._data["progress"] = progress.to_dict()
        self.db._store_item(self, update_only="progress")

    def store_event(
            self,
            type: str,
            text: Optional[str] = None,
            data: Optional[Mapping[str, Any]] = None,
    ):
        self.db._store_event(self, type, text, data)

    def store_exception_event(self, e: Exception, data: Optional[Mapping[str, Any]] = None):
        self.store_event(
            EventType.EXCEPTION,
            text=f"{type(e).__name__}: {e}",
            data={
                **(data or {}),
                "traceback": traceback.format_exc(),
            }
        )

    def events(self, type: Optional[str] = None) -> List[dict]:
        filters = {"process_uuid": self.uuid}
        if type:
            filters["type"] = type
        return list(
            self.db.collection_events()
            .find(filters)
            .sort("timestamp")
        )

    def store_object(
            self,
            object: Union["ModuleObject", dict],
            skipped: bool = False,
    ):
        if not isinstance(object, dict):
            object = object.to_dict()
        self.db._store_object(
            item=self,
            data=object,
            skipped=skipped,
        )

    def kill(self):
        if self.pid:
            try:
                self.log.info(f"Sending SIGTERM to {self.pid}")
                os.kill(self.pid, signal.SIGTERM)
                # self.store_status(ProcessStatus.KILLED)

            except ProcessLookupError:
                self.log.warning(f"Process {self.pid} not found, kill failed")


class ProcessDb(DatabaseMixin):

    def __init__(self):
        super().__init__()
        self.log = logger.Logger("process-db")

        coll = self.collection_events()
        coll.create_index("process_uuid")
        coll.create_index([("date_created", pymongo.ASCENDING)])

        coll = self.collection_objects()
        coll.create_indexes([
            pymongo.IndexModel("process_uuid"),
            pymongo.IndexModel("source_uuid"),
            pymongo.IndexModel([("timestamp", pymongo.ASCENDING)]),
            pymongo.IndexModel([("timestamp", pymongo.DESCENDING)]),
            pymongo.IndexModel("type"),
            pymongo.IndexModel("skipped"),
            pymongo.IndexModel("source_module"),
            pymongo.IndexModel("target_module"),
            pymongo.IndexModel("source_filename"),
            pymongo.IndexModel("target_filename"),
        ])

        coll = self.analysis_results()
        coll.create_indexes([
            pymongo.IndexModel("process_uuid"),
            pymongo.IndexModel("analysis_uuid"),
            pymongo.IndexModel([("timestamp", pymongo.ASCENDING)]),
            pymongo.IndexModel([("timestamp", pymongo.DESCENDING)]),
            pymongo.IndexModel("run_index"),
        ])

    def collection(self) -> Collection:
        return self.database()["process"]

    def collection_events(self) -> Collection:
        return self.database()["process_events"]

    def collection_objects(self) -> Collection:
        return self.database()["process_objects"]

    def analysis_results(self) -> Collection:
        return self.database()["analysis_results"]

    def request_process(
            self,
            name: str,
            kwargs: Optional[Mapping[str, Any]] = None,
            source_uuid: Optional[str] = None,
    ) -> ProcessItem:
        item = ProcessItem(
            db=self,
            name=name,
            uuid=f"p-{uuid.uuid4()}",
            kwargs=kwargs or {},
            source_uuid=source_uuid,
        )
        self._store_item(item)
        return item

    def get_process(self, uuid: str) -> Optional[ProcessItem]:
        item = ProcessItem(db=self, name="unknown", uuid=uuid, kwargs={})
        if self._read_item(item):
            return item

    def get_objects_count(self, process_uuid: str) -> dict:
        """
        Returns processed object counts

        :param process_uuid: str, ID of running or finished process
        :return: dict
            {
                "source": {
                    "<module-uuid>": int,
                },
                "target": {
                    "<module-uuid>": int,
                }
            }
        """
        coll = self.collection_objects()

        def _get_file_count(source: bool):
            source = "source" if source else "target"
            pipeline = [
                {"$match": {"process_uuid": process_uuid}},
                {"$group": {"_id": f"${source}_module", "files": {"$addToSet": f"${source}_filename"}}},
                {"$unwind": "$files"},
                {"$group": {"_id": "$_id", "count": {"$sum": 1}}},
            ]
            return list(coll.aggregate(pipeline))

        return {
            "source": {
                i["_id"]: i["count"]
                for i in _get_file_count(True)
            },
            "target": {
                i["_id"]: i["count"]
                for i in _get_file_count(False)
            },
        }

    def _store_item(self, item: ProcessItem, update_only: Optional[Sequence[str]] = None):
        coll = self.collection()
        if item.status == ProcessStatus.STUB:
            item._data["status"] = ProcessStatus.REQUESTED
            coll.insert_one(item._data)
        else:
            new_data = {
                "status": item.status,
                "pid": item.pid,
                "progress": item._data["progress"],
                "source_object_count": item._data["source_object_count"],
                "date_updated": datetime.datetime.utcnow().isoformat(),
            }
            if update_only:
                new_data = {
                    key: value
                    for key, value in new_data.items()
                    if key in update_only
                }
            coll.update_one(
                {"uuid": item.uuid},
                {"$set": new_data},
            )

    def _read_item(self, item: ProcessItem) -> bool:
        coll = self.collection()
        data = coll.find_one({"uuid": item.uuid})
        if not data:
            return False
        item._data = data
        return True

    def _store_event(
            self,
            item: ProcessItem,
            type: str,
            text: Optional[str] = None,
            data: Optional[Mapping[str, Any]] = None,
    ):
        # self.log.debug(f"store_event({item}, {repr(type)}, {repr(text)}, {repr(data)}")
        coll = self.collection_events()
        coll.insert_one({
            "uuid": f"e-{uuid.uuid4()}",
            "process_uuid": item.uuid,
            "source_uuid": item.source_uuid,
            "type": type,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "text": text,
            "data": data,
        })

    def _store_object(
            self,
            item: ProcessItem,
            data: Mapping[str, Any],
            skipped: bool,
    ):
        coll = self.collection_objects()
        coll.insert_one({
            "uuid": f"o-{uuid.uuid4()}",
            "process_uuid": item.uuid,
            "source_uuid": item.source_uuid,
            "type": data["data_type"],
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "source_filename": data["actions"][0]["data"]["filename"],
            "source_module": data["actions"][0]["module"]["uuid"],
            "target_filename": data["actions"][-1]["data"]["filename"],
            "target_module": data["actions"][-1]["module"]["uuid"],
            "skipped": skipped,
            "data": data,
        })
