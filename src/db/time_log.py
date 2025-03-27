import sqlite3
import zoneinfo
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class TimelogStatus(Enum):
    IN_PROGRESS = 1
    DONE = 2
    CANCELLED = 3


@dataclass
class Timelog:
    task_id: int
    start: datetime
    status: TimelogStatus
    end: Optional[datetime] = None


class ITimelogRepo(ABC):
    pass


class TimelogRepo(ITimelogRepo):
    def __init__(self, sqlitedb: sqlite3.Connection, do_migrate: bool):
        self.sqlitedb = sqlitedb
        if do_migrate:
            self.migrate()

    def migrate(self) -> None:
        stmt = """
        CREATE TABLE IF NOT EXISTS timelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start TIMESTAMP NOT NULL,
            status VARCHAR(255) NOT NULL,
            task_id INTEGER NOT NULL,
            end TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES task(id)
        );
        """
        self.sqlitedb.execute(stmt)
        self.sqlitedb.commit()
