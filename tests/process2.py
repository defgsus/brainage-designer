import os

from bad.process import ProcessBase
from bad.parallel import ProcessWorker


class Process2(ProcessBase):

    name = "test-process-2"

    def run(self):
        if self.kwargs.get("fail"):
            0 / 0
        else:
            with ProcessWorker(2) as pool:
                for i in range(self.kwargs["count"]):
                    pool.put(self._the_task)

    def _the_task(self):
        self.process_item.store_event("info", "from subprocess", {"pid": os.getpid()})


if __name__ == "__main__":
    Process2.run_from_commandline()
