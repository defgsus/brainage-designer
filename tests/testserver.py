import threading
import requests
import time
from pathlib import Path
from typing import Optional, List, Union

from bad.server import Server
from bad.server.serializer import to_json
from bad.process import ProcessScheduler


class TestServer:

    def __init__(self):
        self.server: Optional[Server] = None
        self.scheduler: Optional[ProcessScheduler] = None
        self._threads: List[threading.Thread] = []

    def url(self, *args: str, protocol: str = "http") -> str:
        return self.server.url(*args, protocol=protocol)

    def GET(self, path: str, params: Optional[dict] = None) -> requests.Response:
        return self.request("get", path, params=params)

    def POST(self, path: str, data: Optional[dict] = None) -> requests.Response:
        return self.request("post", path, data=to_json(data) if data else None)

    def request(self, method: str, path: str, expected_status: int = 200, **kwargs) -> requests.Response:
        url = self.url(path)
        response = requests.request(
            method=method,
            url=url,
            **kwargs
        )
        if response.status_code != expected_status:
            raise AssertionError(
                f"Expected status {expected_status}, got {response.status_code}"
                f" for {method.upper()} {url}"
                f"\n\nresponse: {response.content[:1000]}"
            )
        return response

    def start(self):
        if not self._threads:
            self._threads = [
                threading.Thread(name="server-thread", target=self._mainloop_server),
                threading.Thread(name="schedule-thread", target=self._mainloop_scheduler)
            ]
            for t in self._threads:
                t.start()

    def stop(self):
        if self.server:
            self.server.add_callback(self._stop_server)
        if self.scheduler:
            self._stop_scheduler()
        while self._threads:
            self._threads.pop().join()

    def _mainloop_server(self):
        self.server = Server(
            port=5678,
            title="bad-test-server",
        )
        self.server.run()

    def _mainloop_scheduler(self):
        self.scheduler = ProcessScheduler()
        self.scheduler.run()

    def _stop_server(self):
        self.server._io_loop.stop()

    def _stop_scheduler(self):
        self.scheduler.stop()

    def __enter__(self):
        self.start()
        while not self.server._io_loop:
            time.sleep(.1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        time.sleep(.5)

    def create_pipeline(
            self,
            name: str = "Bob Dobbs",
            target_path: Union[str, Path] = "/",
    ) -> "PreprocessPipeline":
        data = self.POST("api/preprocess/", {
            "name": name,
            "target_path": str(target_path),
        }).json()
        pipeline = PreprocessPipeline(self, data["uuid"])

        if target_path:
            assert str(target_path) == data["target_path"], \
                f'{str(target_path)} {data["target_path"]}'

        return pipeline


class PreprocessPipeline:

    def __init__(self, server: TestServer, uuid: str):
        self._server = server
        self.uuid = uuid

    def get_data(self) -> dict:
        return self._server.GET(f"api/preprocess/{self.uuid}/").json()

    def add_module(
            self,
            name: str,
            parameter_values: Optional[dict] = None,
    ) -> dict:
        data = self.get_data()
        data = self._server.POST(
            f"api/preprocess/{self.uuid}",
            {
                **data,
                "modules": (data.get("modules") or []) + [
                    {"name": name}
                ],
            }
        ).json()

        if parameter_values:
            data["modules"][-1]["parameter_values"].update(parameter_values)
            data = self._server.POST(f"api/preprocess/{self.uuid}", data).json()

        return data["modules"][-1]

    def run_process(self) -> dict:
        self.start_process()
        self.wait_process_finished()
        return self.get_data()["latest_process_data"]

    def start_process(self) -> str:
        response = self._server.POST(f"api/preprocess/{self.uuid}/start/")
        return response.json()["process_uuid"]

    def wait_process_finished(self):
        while True:
            data = self.get_data()
            if not data.get("latest_process_data"):
                break

            data = data["latest_process_data"]
            status = data["status"]
            if status in ("finished", "failed"):
                break



