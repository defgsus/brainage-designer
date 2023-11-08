import os
import queue
from multiprocessing import Process, current_process, Manager
from typing import List, Callable

from .workerbase import WorkerBase


class ProcessWorker(WorkerBase):

    def __init__(self, size: int = 0):
        super().__init__(size=size)
        self._manager = Manager()
        self._queue = self._manager.Queue()
        self._processes: List[Process] = []

    def running(self) -> bool:
        return bool(self._processes)

    def stop(self, join_queue: bool = True):
        super().stop(join_queue=False)

    def kill(self):
        for p in self._processes:
            p.terminate()
        for p in self._processes:
            p.join()
        self._processes = []

    def _start(self):
        self._processes = [
            Process(
                name=f"{self.__class__.__name__}-{i+1}/{self.size}",
                target=self._mainloop,
            )
            for i in range(self._size)
        ]
        for p in self._processes:
            p.start()

    def _stop(self):
        for t in self._processes:
            t.join()

    def _mainloop(self):
        while not self._do_stop:
            try:
                action = self._queue.get(timeout=1)
                # print("ACTION", action, self._do_stop)
                if action.get("call"):
                    action["call"]()
                if action.get("stop"):
                    self._do_stop = True
                    self._queue.put({"stop": True})

                self._queue.task_done()
            except queue.Empty:
                pass

        # print("FINISHED", current_process().name)
