import time
from typing import Optional

import sys
import os
from pathlib import Path
import subprocess
import inspect

from bad import config, logger
from bad.process import (
    registered_processes, ProcessStatus, EventType,
    ProcessItem, ProcessDb, Progress
)


class ProcessRunner:
    """
    Runs a registered ProcessBase inside a subprocess.

    A `ProcessItem` must be created by `ProcessDb.request_process` before.
    Status and events of the db process are updated accordingly.
    """
    def __init__(self, name: str, uuid: str):
        self.name = name
        self.uuid = uuid
        try:
            self.process_class = registered_processes[self.name]
        except KeyError:
            raise ValueError(f"process '{self.name}' is not registered")
        self.log = logger.Logger(f"runner/{self.name}/{self.uuid}")
        self.db = ProcessDb()
        self.process: Optional[subprocess.Popen] = None
        self._kill = False

    def process_item(self) -> ProcessItem:
        item = self.db.get_process(self.uuid)
        assert item, f"ProcessRunner called for non-existing process {self.name}/{self.uuid}"
        return item

    def kill(self):
        """
        Kills a running process
        """
        if self.process:
            self._kill = True

    def run(self):
        """
        Execute the `Process` class in a separate process
        """
        self._kill = False

        file_path = Path(inspect.getabsfile(self.process_class))
        root_path = config.BASE_PATH.parent
        python_file = os.path.relpath(file_path, root_path)
        args = [sys.executable, python_file, self.uuid]
        item = self.process_item()

        output, output_err = "", ""
        start_time = time.time()
        try:
            self.log.info("calling subprocess", args)
            # item.store_event(EventType.INFO, "calling subprocess")

            self.process = subprocess.Popen(
                args, cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    "PYTHONPATH": config.BASE_PATH,
                    # push the current config to the process
                    **{
                        f"BAD_{key}": value
                        for key, value in config.to_dict(string_values=True).items()
                    },
                }
            )
            item.store_status(ProcessStatus.STARTED, pid=self.process.pid)
            item.store_event(EventType.STARTED)

            while True:
                if self._kill:
                    self.process.terminate()
                    self.process.wait()
                    break

                if self.process.poll() is not None:  # it's finished
                    break

                try:
                    output_, output_err_ = self.process.communicate(timeout=1)
                    output += output_.decode(errors="ignore")
                    output_err += output_err_.decode(errors="ignore")

                except subprocess.TimeoutExpired:  # keep on running
                    pass

                except ValueError:  # buffer has gone away
                    break

            run_time = time.time() - start_time

            item.store_progress(Progress())

            if self._kill:
                self.log.info(f"subprocess killed after {run_time} seconds")
                item.store_status(ProcessStatus.KILLED)
                item.store_event(EventType.KILLED, data={
                    "stdout": output,
                    "stderr": output_err,
                    "runtime": run_time
                })
            elif self.process.returncode == 0:
                self.log.info(f"subprocess finished after {run_time} seconds")
                item.store_status(ProcessStatus.FINISHED)
                item.store_event(EventType.FINISHED, data={
                    "stdout": output,
                    "stderr": output_err,
                    "runtime": run_time
                })
            elif self.process.returncode in (-9, -15, 247):
                self.log.info(f"subprocess KILLED after {run_time} seconds")
                item.store_status(ProcessStatus.KILLED)
                item.store_event(EventType.KILLED, data={
                    "stdout": output,
                    "stderr": output_err,
                    "runtime": run_time
                })
            else:
                self.log.info(f"subprocess FAILED after {run_time} seconds")
                item.store_status(ProcessStatus.FAILED)
                item.store_event(EventType.FAILED, data={
                    "return_code": self.process.returncode,
                    "stdout": output,
                    "stderr": output_err,
                    "runtime": run_time
                })

        except Exception as e:
            run_time = time.time() - start_time
            self.log.error(f"subprocess failed after {run_time} seconds: {type(e).__name__}: {e}")
            item.store_status(ProcessStatus.FAILED)
            item.store_exception_event(e, data={
                "stdout": output,
                "stderr": output_err,
                "runtime": run_time,
            })
