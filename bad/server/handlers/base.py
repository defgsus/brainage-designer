import json
from typing import Optional, Mapping, Any

import tornado.web
import tornado.websocket

from bad.server import Server
from bad.server.serializer import to_json
from bad.plugins import PluginBase


class BaseHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server: Optional[Server]
        self.plugin: Optional[PluginBase]

    def initialize(self, server: Server, plugin: PluginBase = None):
        self.server = server
        self.plugin = plugin


class WebSocketBaseHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server: Optional[Server]
        self.plugin: Optional[PluginBase]

    def initialize(self, server: Server, plugin: PluginBase = None):
        self.server = server
        self.plugin = plugin


class JsonBaseHandler(BaseHandler):

    def write(self, data: Mapping[str, Any]):
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().write(to_json(data))

    def prepare(self):
        super().prepare()
        try:
            self.json_body = json.loads(self.request.body)
        except ValueError as e:
            self.json_body = None
