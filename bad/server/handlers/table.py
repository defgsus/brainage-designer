import uuid as uuidlib
import datetime
from typing import Optional, List

from tornado.web import HTTPError
from pymongo.database import Collection

from .base import JsonBaseHandler


class TableHandlerMixin:

    columns: List[dict] = None
    default_sort: str = "_id"

    def get_table_data(self, options: dict) -> dict:
        """
        Override and return object with {
            "total": int,
            "total_unfiltered": int,
            "rows": list[dict],
        }
        """
        raise NotImplementedError

    def get_table_options(self) -> dict:
        assert self.columns, f"Must specify {self.__class__.__name__}.columns to render tables"
        options = {
            "limit": 10,
            "offset": 0,
            "sort": self.default_sort,
            "filters": {},
        }
        for name, values in self.request.query_arguments.items():
            for value in values:
                if isinstance(value, bytes):
                    value = value.decode(errors="ignore")

                try:
                    if name == "_limit":
                        options["limit"] = int(value)
                    elif name == "_offset":
                        options["offset"] = int(value)
                    elif name == "_sort":
                        options["sort"] = value
                    else:
                        options["filters"][name] = value
                except (ValueError, IndexError):
                    pass

        return options

    def get_table_columns(self) -> List[dict]:
        ret_columns = []
        for col in self.columns:
            col = {**col}

            if not col.get("type"):
                col["type"] = "str"

            ret_columns.append(col)

        return ret_columns

    def render_table(self):
        options = self.get_table_options()
        table_data = self.get_table_data(options)

        self.write({
            "total": table_data["total"],
            "total_unfiltered": table_data["total_unfiltered"],
            "options": options,
            "columns": self.get_table_columns(),
            "rows": table_data["rows"],
        })
