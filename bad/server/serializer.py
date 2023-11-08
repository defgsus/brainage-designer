import json
import datetime
import math
from pathlib import Path
from typing import Any, Union, Mapping, Optional, Iterator

from pymongo.collection import ObjectId
import numpy as np


class JsonEncoder(json.JSONEncoder):

    def nan_to_none(self, o):
        if isinstance(o, dict):
            return {k: self.nan_to_none(v) for k, v in o.items()}
        elif isinstance(o, (tuple, list)):
            return [self.nan_to_none(v) for v in o]
        elif isinstance(o, float) and math.isnan(o):
            return None
        return o

    def encode(self, o: Any) -> str:
        return super().encode(self.nan_to_none(o))

    def iterencode(self, o: Any, *args, **kwargs) -> Iterator[str]:
        return super().iterencode(self.nan_to_none(o), *args, **kwargs)

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

        elif isinstance(o, (ObjectId, Path)):
            return str(o)

        elif isinstance(o, bytes):
            return o.decode(errors="ignore")

        elif isinstance(o, float):
            return None if math.isnan(o) else o

        try:
            return super().default(o)
        except TypeError:
            pass

        try:
            return int(o)
        except:
            pass

        try:
            float(o)
        except:
            pass

        raise TypeError(f"Object of type '{type(o).__name__}' is not JSON serializable")


def to_json(
        data: Union[Mapping[str, Any], list, tuple],
        **kwargs,
) -> str:
    return json.dumps(
        data,
        cls=JsonEncoder,
        separators=(",", ":"),
        ensure_ascii=False,
        **kwargs,
    )
