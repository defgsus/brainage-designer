import datetime
import json
import time
import inspect
from typing import Optional, Dict, Sequence, Union, List, Callable

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.routing

from bad import config, logger
from bad.plugins import PluginBase, registered_plugins
from bad.db import DatabaseMixin


class Server(DatabaseMixin):

    def __init__(
            self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            title: str = "bad-server",
    ):
        super().__init__()
        self.host = host if host is not None else config.SERVER_HOST
        self.port = port if port is not None else config.SERVER_PORT
        self.title = title

        self.log = logger.Logger(self.title)

        self._app: Optional[tornado.web.Application] = None
        self._io_loop: Optional[tornado.ioloop.IOLoop] = None
        self._callbacks: List[Callable] = []
        self._started_at: Optional[datetime.datetime] = None

        self._plugins: Dict[str, PluginBase] = {}

    def url(self, *args: str, protocol: str = "http") -> str:
        url = f"{protocol}://{self.host}:{self.port}"
        if args:
            url = "/".join((url, *(str(a) for a in args)))
        return url

    def run(self):
        self._mainloop()

    def terminate(self):
        for p in self._plugins.values():
            p.terminate()

    @property
    def running(self) -> bool:
        return bool(self._io_loop)

    def add_callback(self, callback: Callable):
        # assert self._io_loop, f"{self}.add_callback() called with stopped server"
        if not self._io_loop:
            self._callbacks.append(callback)
        else:
            self._io_loop.add_callback(callback)

    def send_message(
            self,
            name: str,
            data: Optional[Union[dict, list]] = None,
            client: Optional[Union[str, tornado.websocket.WebSocketHandler]] = None,
    ):
        """
        Send a websocket message to all connected clients.

        :param name: str, message name
        :param data: json serializable data
        :param client: optional client or client_id to which to send the message instead of all clients
        """
        self.call_plugin("websocket", "send_message", name=name, data=data, client=client)

    def call_plugin(self, _plugin_name: str, _function_name: str, **kwargs):
        plugin = self._plugins.get(_plugin_name)
        if plugin:
            func = getattr(plugin, _function_name, None)
            if callable(func):
                return func(**kwargs)
        self.log.error(
            f"call_plugin({repr(_plugin_name)}, {repr(_function_name)}) did not match"
        )

    def status(self) -> dict:
        return {
            "title": self.title,
            "startet_at": self._started_at,
            "plugins": sorted(self._plugins.keys()),
            "num_clients": len(self._plugins["websocket"].clients) if self._plugins.get("websocket") else 0,
        }

    def _mainloop(self):
        from bad.plugins.essential.index import IndexFallbackHandler
        from . import handlers
        self._started_at = datetime.datetime.utcnow()
        self._io_loop = tornado.ioloop.IOLoop()
        self._io_loop.make_current()

        self._plugins = {
            name: plugin_class(self)
            for name, plugin_class in registered_plugins.items()
        }

        self._url_handlers = self._create_url_handlers()
        self._app = tornado.web.Application(
            handlers=self._url_handlers,
            default_host=self.host,
            static_path=str(config.STATIC_PATH),
            template_path=str(config.TEMPLATE_PATH),
            debug=config.DEBUG,
            static_handler_class=handlers.NoCacheStaticFileHandler,
            default_handler_class=IndexFallbackHandler,
        )
        self._app.listen(self.port)
        self.log.info(self.info_str())

        while self._callbacks:
            self._io_loop.add_callback(self._callbacks.pop())

        self._io_loop.start()
        self._io_loop.close()

        self._io_loop = None
        self._app = None

    def info_str(self) -> str:
        handler_lines = sorted(
            (
                [str(h[0]), str(h[1]).split("'")[1]]
                for h in self._url_handlers
            ),
            key=lambda h: h[0]
        )
        max_len = max(1, *(len(h[0]) for h in handler_lines))
        return (
            f"\napi-server   {self.url()}"
            f"\ndatabase:    {config.DATABASE_HOST}:{config.DATABASE_PORT}/{config.DATABASE_NAME}"
            f"\nstatic path: {config.STATIC_PATH}"
            f'\nplugins:     {", ".join(sorted(self._plugins.keys()))}'
            f'\nhandlers:\n' + "\n".join(f"{l[0]:{max_len}} {l[1]}" for l in handler_lines)
        )

    def _create_url_handlers(self) -> list:
        from .handlers import BaseHandler, WebSocketBaseHandler
        handlers = [
            #(r"/img/([a-z0-9_\-]+)/([0-9]+).png", handlers.ImageHandler, {"server": self}),
        ]
        for plugin in self._plugins.values():
            for handler_t in (plugin.get_handlers() or []):
                init_params = {}
                if issubclass(handler_t[1], (BaseHandler, WebSocketBaseHandler)):
                    init_params.update({"server": self, "plugin": plugin})
                if len(handler_t) > 2:
                    init_params.update(handler_t[2])
                handlers.append((
                    handler_t[0],
                    handler_t[1],
                    init_params,
                ))
        return handlers

    def _handle_websocket_message(self, client_id: str, name: str, data: dict) -> bool:
        handled = False

        name_parts = name.split(":")
        if len(name_parts) == 3:
            plugin_name, uuid, what = name_parts
            for plugin in self._plugins.values():
                if plugin_name == plugin.name:
                    func = getattr(plugin, f"on_websocket_{what}", None)
                    if callable(func):
                        func(client_id, uuid, data)
                        handled = True

        for plugin in self._plugins.values():
            handled |= plugin.handle_websocket_message(client_id, name, data)

        return handled
