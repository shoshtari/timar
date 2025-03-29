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
    id: int
    task_id: int
    start: datetime
    status: TimelogStatus
    end: Optional[datetime] = None
    metadata: Optional[str] = None

    @property
    def eclapsed_time(self) -> str:
        end = self.end or datetime.now()
        eclapsed = (end - self.start).total_seconds()

        eclapsed_str = ""
        if hour := int(eclapsed // 3600):
            eclapsed_str += f"{hour} ساعت "
        eclapsed = eclapsed % 3600
        if minute := int(eclapsed // 60):
            eclapsed_str += f"{minute} دقیقه "
        eclapsed = eclapsed % 60
        if seconds := int(eclapsed):
            eclapsed_str += f"{seconds} ثانیه "

        return eclapsed_str


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

    def get_in_progress_logs(self) -> List[Timelog]:
        stmt = """
        SELECT id, task_id, start, status, metadata
        FROM timelog
        WHERE status = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (TimelogStatus.IN_PROGRESS.name,))
        rows = cursor.fetchall()
        ans = []
        for row in rows:
            ans.append(
                Timelog(
                    id=row[0],
                    task_id=row[1],
                    start=datetime.fromisoformat(row[2]),
                    status=row[3],
                    metadata=row[4],
                ),
            )
        return ans

    def get_by_id(self, timelog_id: int) -> Timelog:
        stmt = """
        SELECT id, task_id, start, status, metadata, end
        FROM timelog
        WHERE id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (timelog_id,))
        row = cursor.fetchall()[0]

        return Timelog(
            id=row[0],
            task_id=row[1],
            start=datetime.fromisoformat(row[2]),
            status=row[3],
            metadata=row[4],
            end=datetime.fromisoformat(row[5]),
        )

    def set_end_if_not_exists(self, timelog_id: int, end: datetime) -> None:
        stmt = """
        UPDATE timelog SET end = ?, status = ? WHERE id = ?
        """
        self.sqlitedb.execute(
            stmt,
            (end.isoformat(), TimelogStatus.DONE.name, timelog_id),
        )
        self.sqlitedb.commit()
