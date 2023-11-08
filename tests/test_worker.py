import unittest
from pathlib import Path
import time
import uuid
import tempfile
import glob
from bad.parallel import ThreadWorker, ProcessWorker


def _process_callback(dir: str):
    (Path(dir) / str(uuid.uuid4())).write_text("1")

THREADS_JOBS_SCENARIOS = [
    (4, 10),
    (10, 4),
]

class TestWorker(unittest.TestCase):

    def test_thread_worker(self):
        for num_threads, num_jobs in THREADS_JOBS_SCENARIOS:
            data = {}
            def _callback():
                data[str(uuid.uuid4())] = 1

            with ThreadWorker(num_threads) as pool:
                for i in range(num_jobs):
                    pool.put(_callback)

            self.assertEqual(num_jobs, len(data))

    def test_process_worker(self):
        for num_threads, num_jobs in THREADS_JOBS_SCENARIOS:

            with tempfile.TemporaryDirectory(prefix="bad-test-worker") as tmp_dir:
                self.assertTrue(Path(tmp_dir).exists())

                with ProcessWorker(num_threads) as pool:
                    for i in range(num_jobs):
                        pool.put(_process_callback, dir=tmp_dir)

                pattern = str(Path(tmp_dir) / "*")
                self.assertEqual(num_jobs, len(glob.glob(pattern)))
