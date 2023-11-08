from typing import Optional, List


class ModuleObjectType:
    FILE = "file"
    IMAGE = "image"

    all = [FILE, IMAGE]


class ModuleObject:
    data_type: str = None

    def __init__(
            self,
            actions: Optional[List[dict]] = None,
            source: Optional[dict] = None,
    ):
        assert self.data_type, f"Need to define '{self.__class__.__name__}.data_type'"
        self.source: Optional[dict] = source
        self.actions: List[dict] = actions or []

    def discard(self):
        """Override to free memory"""
        pass

    def to_dict(self) -> dict:
        return {
            "object_class": self.__class__.__name__,
            "data_type": self.data_type,
            "runtime_id": id(self),
            "actions": self.actions,
            "source": self.source,
        }
