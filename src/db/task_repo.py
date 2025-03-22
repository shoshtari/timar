import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Task:
    name: str
    description: str
    epic_id: int
    id: Optional[int] = None


class ITaskRepo(ABC):
    @abstractmethod
    def create(self, task: Task) -> int:
        raise NotImplementedError


class TaskRepo(ITaskRepo):
    def __init__(self, sqlitedb: sqlite3.Connection, do_migrate: bool):
        self.sqlitedb = sqlitedb
        if do_migrate:
            self.migrate()

    def migrate(self) -> None:
        stmt = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            epic_id INTEGER NOT NULL,
            FOREIGN KEY(epic_id) REFERENCES epics(id)
        );
        """
        self.sqlitedb.execute(stmt)

    def create(self, task: Task) -> int:
        stmt = """
        INSERT INTO tasks (name, description, epic_id)
        VALUES (?, ?, ?)
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (task.name, task.description, task.epic_id))
        out = cursor.lastrowid
        if out is None:
            raise ValueError("couldn't get id of inserted row")
        return out
