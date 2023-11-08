import uuid
import json
from functools import partial
from typing import Optional, Iterable, Union

import tornado.websocket

from bad.plugins import PluginBase
from bad.server.handlers import WebSocketBaseHandler


class WebSocketHandler(WebSocketBaseHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin: WebSocketPlugin
        self.client_id = str(uuid.uuid4())

    def __repr__(self):
        return self.client_id

    def check_origin(self, origin):
        return True

    def open(self, *args: str, **kwargs: str):
        self.plugin._add_client(self)

    def on_message(self, message):
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            raise IOError(f"Invalid websocket message: '{message[:100]}'")

        self.plugin._on_message(self, message)

    def on_close(self):
        self.plugin._remove_client(self)


class WebSocketPlugin(PluginBase):
    name = "websocket"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients = dict()

    def get_handlers(self) -> Optional[Iterable]:
        return [
            (r"/api/ws/?", WebSocketHandler),
        ]

    def send_message(
            self,
            name: str,
            data: Optional[Union[dict, list]] = None,
            client: Optional[Union[str, WebSocketHandler]] = None,
    ):
        """
        Send a websocket message to one or all connected clients.

        :param name: str, message name
        :param data: json serializable data
        :param client: optional client or client_id to which to send the message instead of all clients
        """
        message = json.dumps({"name": name, "data": data})
        self.server.add_callback(partial(self._send_message, message, client))

    def _send_message(
            self,
            message: str,
            client: Optional[Union[str, WebSocketHandler]] = None,
    ):
        if client:
            if isinstance(client, str):
                client = self.clients[client]
            client.write_message(message)
        else:
            for client_id, client in self.clients.items():
                client.write_message(message)

    def _add_client(self, client: WebSocketHandler):
        self.log.debug("new client", client)
        self.clients[client.client_id] = client
        self.send_message("welcome", {"client_id": client.client_id}, client)

    def _remove_client(self, client: WebSocketHandler):
        self.log.debug("remove client", client)
        self.clients.pop(client.client_id, None)

    def _on_message(self, client: WebSocketHandler, message: dict):
        self.log.debug(client.client_id, "received", message)
        name, data = message["name"], message.get("data") or {}

        if not self.server._handle_websocket_message(client.client_id, name, data):
            self.log.warning(f"Unhandled client-message '{name}', {data}")




