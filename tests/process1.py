from bad import config
from bad.process import ProcessBase


class Process1(ProcessBase):

    name = "test-process-1"

    def run(self):
        if self.kwargs.get("fail"):
            0 / 0
        else:
            self.process_item.store_event("info", "hello", {"process1": "was running"})


if __name__ == "__main__":
    Process1.run_from_commandline()
