import json
import uuid
import datetime
import time
import signal
from typing import Dict, Generator, Iterable, List, Optional
from functools import partial

import numpy as np

from bad import config
from bad.process import ProcessBase, EventType, Progress
from bad.modules import *
from bad.parallel import ProcessWorker

from bad.plugins.analysis.reduction import AnalysisReduction
from bad.plugins.analysis.analysis import Analysis



class AnalysisProcess(ProcessBase):
    name = "analysis"

    def run(self):
        # print(json.dumps(self.kwargs, indent=2))
        plugin = self.kwargs["plugin"]

        modules = [
            ModuleFactory.new_module(
                name=mod["name"],
                parameters=mod["parameter_values"],
            )
            for mod in plugin["modules"]
        ]

        analysis_model = None
        for m in modules:
            m.prepare()
            if isinstance(m, AnalysisModelBase):
                analysis_model = m

        assert analysis_model, "Need to select an analysis model"

        reduction = AnalysisReduction(
            modules=modules,
            separation_values=plugin.get("separation_values") or None,
            reduction_values=plugin.get("reduction_values") or None,
        )
        reduction.init()

        assert reduction.valid_files(), "No valid source files found"

        self.analysis = Analysis(
            reduction=reduction,
            analysis_model=analysis_model,
            form_values=plugin["analysis_values"],
            run_callback=self._run_callback,
        )

        self.analysis.train()

    def _run_callback(self, run: dict):
        timestamp = datetime.datetime.utcnow().isoformat()
        plugin = self.kwargs["plugin"]

        coll = self.process_item.db.analysis_results()

        coll.insert_one({
            **run,
            "uuid": f"ar-{uuid.uuid4()}",
            "process_uuid": self.uuid,
            "analysis_uuid": plugin["uuid"],
            "timestamp": timestamp,
        })

    def kill(self):
        pool = getattr(self, "_pool", None)
        if pool:
            pool.kill()
            self._pool = None


def main():
    proc = AnalysisProcess.create_from_commandline()

    def on_terminate(sig_num, stack_frame):
        proc.log.info("SIGTERM received")
        proc.kill()
        exit(-9)  # tell ProcessRunner that we were killed

    signal.signal(signal.SIGTERM, on_terminate)

    proc.run_and_catch()


if __name__ == "__main__":
    main()
