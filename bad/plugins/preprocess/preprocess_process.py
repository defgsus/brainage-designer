import time
import signal
from typing import Dict, Generator, Iterable, List, Optional
from functools import partial

import numpy as np

from bad import config
from bad.process import ProcessBase, EventType, Progress
from bad.modules import *
from bad.parallel import ProcessWorker

import bad.plugins.preprocess


class PreprocessingProcess(ProcessBase):
    name = "preprocessing"

    def run(self):
        graph = self.create_module_graph()
        if not graph.source_modules:
            self.process_item.store_event(EventType.ERROR, "quit because no source is defined")
            return
        #if not graph.process_modules:
        #    self.process_item.store_event("error", "quit because no processing is defined")
        #    return

        self.process_item.store_progress(Progress("preparing modules"))
        graph.prepare_modules()
        source_object_count_map = graph.get_source_object_counts()
        self.process_item.store_source_object_count(source_object_count_map)

        num_processes = self.kwargs["plugin"].get("num_processes") or 1

        run_graph_kwargs = {
            "graph": graph,
        }

        self.process_item.store_progress(Progress("running pipeline"))
        if num_processes <= 1:
            self._run_graph(**run_graph_kwargs)
        else:
            with ProcessWorker(num_processes) as pool:
                self._pool = pool
                for i in range(pool.size):
                    pool.put(partial(
                        self._run_graph,
                        **run_graph_kwargs,
                        interval=pool.size,
                        offset=i,
                    ))
            self._pool = None

    def kill(self):
        pool = getattr(self, "_pool", None)
        if pool:
            pool.kill()
            self._pool = None

    def _run_graph(
            self,
            graph: ModuleGraph,
            interval: int = 1,
            offset: int = 0,
    ):
        def _existing_target_callback(data: dict):
            self.process_item.store_object(
                data, skipped=True,
            )

        for processed_object in graph.process(
                source_types=["image"],
                interval=interval,
                offset=offset,
                existing_target_callback=_existing_target_callback,
        ):
            self.process_item.store_object(
                processed_object.to_dict(),
            )
            processed_object.discard()

        self.process_item.store_event(
            EventType.GRAPH_RESULT,
            data={
                "sub_process": offset,
                "report": graph.report,
            },
        )


def main():
    proc = PreprocessingProcess.create_from_commandline()

    def on_terminate(sig_num, stack_frame):
        proc.log.info("SIGTERM received")
        proc.kill()
        exit(-9)  # tell ProcessRunner that we were killed

    signal.signal(signal.SIGTERM, on_terminate)

    proc.run_and_catch()


if __name__ == "__main__":
    main()