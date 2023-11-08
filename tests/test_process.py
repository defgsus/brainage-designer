import unittest
import json
from typing import Optional, Iterable

from bad.process import *
from bad.server.serializer import to_json

# register test processes
from tests import process1
from tests import process2


class TestProcess(unittest.TestCase):

    def create_process(
            self,
            db: ProcessDb,
            name: str,
            kwargs: Optional[dict] = None,
            source_uuid: Optional[str] = None,
    ) -> ProcessItem:
        proc = db.request_process(
            name=name, kwargs=kwargs, source_uuid=source_uuid,
        )
        self.assertEqual(ProcessStatus.REQUESTED, proc.status)
        self.assertEqual(name, proc.name)
        self.assertEqual(kwargs or {}, proc.kwargs)
        self.assertEqual(source_uuid, proc.source_uuid)
        self.assertGreater(len(proc.uuid), 20)
        return proc

    def dump_events(self, events: Iterable[dict]):
        for e in events:
            print(to_json(e, indent=2))

    def test_process_runner(self):
        db = ProcessDb()
        proc = self.create_process(
            db,
            name="test-process-1",
            kwargs={"special": "parameters"},
            source_uuid="123",
        )

        # -- run --

        runner = ProcessRunner("test-process-1", proc.uuid)
        runner.run()

        events = proc.events()
        self.dump_events(events)
        self.assertEqual(EventType.STARTED, events[0]["type"])
        self.assertEqual(EventType.INFO, events[1]["type"])
        self.assertEqual(EventType.FINISHED, events[2]["type"], f"Got: {events[2]}")

        self.assertEqual("hello", events[1]["text"])
        self.assertEqual({"process1": "was running"}, events[1]["data"])

    def test_process_runner_fail(self):
        db = ProcessDb()
        proc = self.create_process(
            db,
            name="test-process-1",
            kwargs={"fail": True},  # trigger a divide by zero
        )

        # -- run --

        runner = ProcessRunner("test-process-1", proc.uuid)
        runner.run()

        events = proc.events()
        #self.dump_events(events)

        self.assertEqual(EventType.STARTED, events[0]["type"])
        self.assertEqual(EventType.EXCEPTION, events[1]["type"])
        self.assertTrue(events[1]["text"].startswith("ZeroDivisionError:"))
        # also subprocess failed
        self.assertEqual(EventType.FAILED, events[2]["type"])

        self.assertEqual(ProcessStatus.FAILED, proc.update_from_db().status)

    def test_process_runner_with_subprocesses(self):
        db = ProcessDb()
        proc = self.create_process(
            db,
            name="test-process-2",
            kwargs={"count": 4},
            source_uuid="123",
        )

        # -- run --

        runner = ProcessRunner("test-process-2", proc.uuid)
        runner.run()

        events = proc.events()
        # self.dump_events(events)

        self.assertEqual(EventType.STARTED, events[0]["type"])
        for i in range(proc.kwargs["count"]):
            self.assertEqual(EventType.INFO, events[1 + i]["type"])
            self.assertIn("pid", events[1 + i]["data"])
        self.assertEqual(EventType.FINISHED, events[1 + i + 1]["type"], f"Got: {events[1 + i + 1]}")
