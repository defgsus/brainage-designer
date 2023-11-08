import time
from typing import Optional

from bad import logger
from bad.process import ProcessDb, ProcessStatus, ProcessRunner


class ProcessScheduler:
    """
    Runs 'forever' and picks and runs requested processes from the database
    """
    def __init__(self):
        self.db = ProcessDb()
        self.log = logger.Logger("scheduler")
        self._do_stop = False
        self._runner: Optional[ProcessRunner] = None

    def run(self):
        self.log.info("started")
        self._do_stop = False
        while not self._do_stop:
            requested_procs = list(
                self.db.collection()
                .find({"status": ProcessStatus.REQUESTED})
                .sort("date_created")
                .limit(1)
            )
            if not requested_procs:
                # self.log.debug("idle..")
                time.sleep(1)
                continue

            name, uuid = requested_procs[0]["name"], requested_procs[0]["uuid"]
            self._run_process(name, uuid)

    def stop(self):
        self._do_stop = True

    def _run_process(self, name: str, uuid: str):
        self.log.debug("running", name, uuid)
        self._runner = ProcessRunner(name, uuid)
        self._runner.run()
        self._runner = None

    def kill(self, uuid: str) -> bool:
        if self._runner and self._runner.uuid == uuid:
            self._runner.kill()
            return True
        else:
            return False


if __name__ == "__main__":
    ProcessScheduler().run()
