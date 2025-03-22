import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Epic:
    name: str
    description: str
    id: Optional[int] = None


class IEpicRepo(ABC):
    @abstractmethod
    def create(self, e: Epic) -> int:
        raise NotImplementedError


class EpicRepo(IEpicRepo):
    def __init__(self, sqlitedb: sqlite3.Connection, do_migrate: bool):
        self.sqlitedb = sqlitedb
        if do_migrate:
            self.migrate()

    def migrate(self) -> None:
        stmt = """
        CREATE TABLE IF NOT EXISTS epic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
        """
        self.sqlitedb.execute(stmt)

    def create(self, epic: Epic) -> int:
        stmt = """
        INSERT INTO epic (name, description)
        VALUES (?, ?)
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (epic.name, epic.description))
        out = cursor.lastrowid
        if out is None:
            raise ValueError("couldn't get id of inserted row")
        return out
