from typing import Optional, Iterable

from bad.plugins import PluginBase
from bad.server.handlers import JsonBaseHandler


class DashboardPlugin(PluginBase):
    name = "dashboard"

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/api/dashboard/", DashboardHandler),
            (r"/api/status/", StatusHandler),
        ]

    def status(self) -> dict:
        status = {
            "server": self.server.status(),
        }
        return status


class DashboardHandler(JsonBaseHandler):

    def get(self):
        self.write({"all": "fine"})


class StatusHandler(JsonBaseHandler):

    def get(self):
        self.write(self.plugin.status())
