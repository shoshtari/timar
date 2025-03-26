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

    @abstractmethod
    def get_by_chat_id(self, chat_id: int) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task:
        raise NotImplementedError

    @abstractmethod
    def get_owner_chat(self, task_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete(self, task_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def edit(self, id: int, col: str, value: str) -> None:
        raise NotImplementedError


class TaskRepo(ITaskRepo):
    def __init__(self, sqlitedb: sqlite3.Connection, do_migrate: bool):
        self.sqlitedb = sqlitedb
        if do_migrate:
            self.migrate()

    def migrate(self) -> None:
        stmt = """
        CREATE TABLE IF NOT EXISTS task (
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
        INSERT INTO task (name, description, epic_id)
        VALUES (?, ?, ?)
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (task.name, task.description, task.epic_id))
        out = cursor.lastrowid
        if out is None:
            raise ValueError("couldn't get id of inserted row")
        self.sqlitedb.commit()
        return out

    def get_by_chat_id(self, chat_id: int) -> List[Task]:
        stmt = """
        SELECT id, name, description, epic_id
        FROM task
        WHERE epic_id IN
        (SELECT id FROM epic WHERE chat_id = ?)
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (chat_id,))
        return [
            Task(id=row[0], name=row[1], description=row[2], epic_id=row[3])
            for row in cursor.fetchall()
        ]

    def get_by_id(self, task_id: int) -> Task:
        stmt = """
        SELECT id, name, description, epic_id
        FROM task
        WHERE id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (task_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("task not found")
        return Task(id=row[0], name=row[1], description=row[2], epic_id=row[3])

    def get_owner_chat(self, task_id: int) -> int:
        stmt = """
        SELECT chat_id
        FROM epic
        WHERE id = (
            SELECT epic_id
            FROM task
            WHERE id = ?
        )
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (task_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("task not found")
        return row[0]

    def delete(self, task_id: int) -> None:
        stmt = """
DELETE FROM task WHERE id = ?
"""
        self.sqlitedb.execute(stmt, (task_id,))
        self.sqlitedb.commit()

    def edit(self, id: int, col: str, value: str) -> None:
        if col not in ("name", "description"):
            raise ValueError(f"invalid column: {col}")
        stmt = f"UPDATE task SET {col} = ? WHERE id = ?"
        self.sqlitedb.execute(stmt, (value, id))
        self.sqlitedb.commit()
