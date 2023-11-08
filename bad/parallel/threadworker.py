import os
import threading
import queue
from typing import List, Callable

from .workerbase import WorkerBase


class ThreadWorker(WorkerBase):

    def __init__(self, size: int = 0):
        super().__init__(size=size)
        self._threads: List[threading.Thread] = []

    def running(self) -> bool:
        return bool(self._threads)

    def _start(self):
        self._threads = [
            threading.Thread(name=f"{self.__class__.__name__}-{i+1}/{self.size}", target=self._mainloop)
            for i in range(self._size)
        ]
        for t in self._threads:
            t.start()

    def _stop(self):
        for t in self._threads:
            t.join()
