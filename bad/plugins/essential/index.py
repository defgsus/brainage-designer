from typing import Optional, Iterable

from bad import config
from bad.plugins import PluginBase
from bad.server.handlers import BaseHandler, NoCacheStaticFileHandler


class IndexPlugin(PluginBase):
    name = "index"

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/()", NoCacheStaticFileHandler, {"path": str(config.STATIC_PATH / "index.html")}),
            (r"/(index[.a-z0-9]+)", NoCacheStaticFileHandler, {"path": str(config.STATIC_PATH)}),
            (r"/(brain[.a-z0-9]+)", NoCacheStaticFileHandler, {"path": str(config.STATIC_PATH)}),
        ]


class IndexFallbackHandler(NoCacheStaticFileHandler):

    # just make path parameter optional, it's not used
    def initialize(self, path: str = "/", default_filename: Optional[str] = None) -> None:
        super().initialize(path=path, default_filename=default_filename)

    def get(self, *args, **kwargs):
        return super().get(str(config.STATIC_PATH / "index.html"))
