from threading import current_thread
from urllib.parse import quote_plus
from typing import Dict

from pymongo import MongoClient
from pymongo.database import Database

from bad import config, logger


class DatabaseMixin:

    def __init__(self, *args, **kwargs):
        self._db_clients: Dict[str, MongoClient] = {}

    def database(self) -> Database:
        return self.database_client()[config.DATABASE_NAME]

    def database_client(self) -> MongoClient:
        key = current_thread().name
        if key not in self._db_clients:
            host = config.DATABASE_HOST
            port = config.DATABASE_PORT
            if config.DATABASE_USER:
                host = "mongodb://{}:{}@{}".format(
                    quote_plus(config.DATABASE_USER),
                    quote_plus(config.DATABASE_PASSWORD),
                    config.DATABASE_HOST
                )
            self._db_clients[key] = MongoClient(
                host=host, port=port,
                directConnection=True,
                socketTimeoutMS=2_000,
                connectTimeoutMS=2_000,
                retryReads=False,
            )
        return self._db_clients[key]
