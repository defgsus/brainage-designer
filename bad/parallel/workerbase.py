import os
import queue
from threading import current_thread
from multiprocessing import current_process
from functools import partial
from typing import List, Callable


class WorkerBase:

    def __init__(self, size: int = 0):
       self._do_stop = None
       self._queue = queue.Queue()
       self._size = size or os.cpu_count()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def size(self) -> int:
        return self._size

    def running(self) -> bool:
        raise NotImplementedError

    def start(self):
        if self.running():
            return

        self._do_stop = False
        self._start()

    def stop(self, join_queue: bool = True):
        if not self.running() or self._do_stop:
            return

        self._queue.put({"stop": True})

        if join_queue:
            self._queue.join()

        self._do_stop = True
        self._stop()

    def put(self, callable: Callable, *args, **kwargs):
        if args or kwargs:
            callable = partial(callable, *args, **kwargs)
        self._queue.put_nowait({"call": callable})

    def _start(self):
        raise NotImplementedError

    def _stop(self):
        raise NotImplementedError

    def _mainloop(self):
        while not self._do_stop:
            try:
                action = self._queue.get(timeout=1)
                if action.get("call"):
                    action["call"]()
                if action.get("stop"):
                    self._do_stop = True

                self._queue.task_done()
            except queue.Empty:
                pass
