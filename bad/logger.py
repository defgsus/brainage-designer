import sys
import io
import datetime


DEBUG = 1
INFO = 2
WARNING = 3
ERROR = 4


class Logger:

    def __init__(self, name: str):
        self._name = name

    def log(self, level: int, *args):
        file = io.StringIO()
        print(self._prefix(level), *args, file=file)
        file.seek(0)
        sys.stderr.write(file.read())
        sys.stderr.flush()

    def debug(self, *args):
        self.log(DEBUG, *args)

    def info(self, *args):
        self.log(INFO, *args)

    def warning(self, *args):
        self.log(WARNING, *args)

    def error(self, *args):
        self.log(ERROR, *args)

    def _prefix(self, level: int):
        dt = datetime.datetime.utcnow()
        return f"{dt.isoformat()}: {level}: {self._name}:"


log = Logger("main")
