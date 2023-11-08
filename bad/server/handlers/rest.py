import json
import uuid as uuidlib
from copy import deepcopy
import datetime
from typing import Optional, Mapping, Any

import pymongo
from tornado.web import HTTPError
from pymongo.database import Collection

from .base import JsonBaseHandler
from .table import TableHandlerMixin


class DbRestHandler(TableHandlerMixin, JsonBaseHandler):
    """
    Generalized REST interface
    """
    collection_name: str = None
    uuid_prefix: str = None

    def __init__(self, *args, **kwargs):
        assert self.collection_name, f"{self.__class__.__name__}.collection_name must be specified"
        assert self.uuid_prefix, f"{self.__class__.__name__}.uuid_prefix must be specified"
        super().__init__(*args, **kwargs)

    def collection(self) -> Collection:
        """
        Access to the mongodb collection
        :return: pymongo.database.Collection instance
        """
        return self.server.database()[self.collection_name]

    def before_db_insert(self, obj: dict) -> None:
        """
        Override to add additional data to obj before saving to database.
        Parameters "uuid", "date_created" and the json-body of the post-request
        are already set.
        """
        pass

    def after_db_read(self, obj: dict) -> None:
        pass

    def get(self, uuid):
        if uuid == "table" and self.columns:
            self.render_table()
        else:
            self.render_object(uuid)

    def render_object(self, uuid: str) -> Optional[dict]:
        coll = self.collection()
        obj = coll.find_one({"uuid": uuid})
        if not obj:
            self.set_status(404)
            self.write({"detail": "Not found"})
            self.finish()
            return

        db_data = {**obj}
        self.after_db_read(db_data)
        self.write(db_data)

    def post(self, uuid):
        if not self.json_body:
            self.write({"detail": "No JSON data"})
            self.set_status(400)
            return

        coll = self.collection()

        if not uuid:

            document = {
                **self.json_body,
                "uuid": f"{self.uuid_prefix}-{uuidlib.uuid4()}",
                "date_created": datetime.datetime.utcnow().isoformat(),
            }
            self.before_db_insert(document)
            coll.insert_one(document)

            uuid = document["uuid"]
        else:
            update_data = deepcopy(self.json_body)
            self.before_db_insert(update_data)
            update_data.pop("_id", None)
            update_data.pop("uuid", None)

            coll.update_one({"uuid": uuid}, {"$set": update_data})

        self.render_object(uuid)

    def delete(self, uuid):
        coll = self.collection()

        result = coll.delete_one({"uuid": uuid})
        if result.deleted_count:
            self.set_status(204)
        else:
            self.set_status(404)
            self.write({"detail": "Not found"})

    def get_table_data(self, options: dict) -> dict:
        result = {}
        coll = self.collection()
        filters = self._transform_filters(options["filters"])

        result["total_unfiltered"] = coll.count_documents({})
        result["total"] = coll.count_documents(filters) if filters else result["total_unfiltered"]

        sort_field = options["sort"] or self.default_sort
        sort_order = pymongo.ASCENDING
        if sort_field.startswith("-"):
            sort_field = sort_field[1:]
            sort_order = pymongo.DESCENDING
        query = coll.find(filters).sort(sort_field, sort_order)

        if options["offset"]:
            query = query.skip(options["offset"])
        if options["limit"]:
            query = query.limit(options["limit"])

        # print(json.dumps(query.explain(), indent=2))

        result["rows"] = list(query)
        return result

    def _transform_filters(self, filters: dict):
        mongo_filters = {}
        for key, value in filters.items():
            # value = {"$eq": value}
            mongo_filters[key] = value
        return mongo_filters
