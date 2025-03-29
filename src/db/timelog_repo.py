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
    metadata: Optional[str] = None


class ITimelogRepo(ABC):
    @abstractmethod
    def create(self, task_id: int, start_time: datetime) -> int:
        raise NotImplementedError

    @abstractmethod
    def set_metadata(self, timelog_id: int, metadata: str) -> None:
        raise NotImplementedError


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
            metadata TEXT DEFAULT NULL,
            FOREIGN KEY (task_id) REFERENCES task(id)
        );
        """
        self.sqlitedb.execute(stmt)
        self.sqlitedb.commit()

    def create(self, task_id: int, start: datetime) -> int:
        stmt = """
        INSERT INTO timelog (task_id, start, status)
        VALUES (?, ?, ?)
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(
            stmt,
            (task_id, start.isoformat(), TimelogStatus.IN_PROGRESS.name),
        )
        self.sqlitedb.commit()
        res = cursor.lastrowid
        if res is None:
            raise ValueError("return value is none")
        return res

    def set_metadata(self, timelog_id: int, metadata: str) -> None:
        stmt = """
        UPDATE timelog SET metadata = ? WHERE id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (metadata, timelog_id))
        self.sqlitedb.commit()
