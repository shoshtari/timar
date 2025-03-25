import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Epic:
    name: str
    description: str
    chat_id: int
    id: Optional[int] = None


class IEpicRepo(ABC):
    @abstractmethod
    def create(self, e: Epic) -> int:
        raise NotImplementedError

    def get_by_chat_id(self, chat_id: int) -> List[Epic]:
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
            chat_id INTEGER,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
        """
        self.sqlitedb.execute(stmt)

    def create(self, epic: Epic) -> int:
        stmt = """
        INSERT INTO epic (chat_id, name, description)
        VALUES (?, ?, ?)
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (epic.chat_id, epic.name, epic.description))
        out = cursor.lastrowid
        if out is None:
            raise ValueError("couldn't get id of inserted row")
        self.sqlitedb.commit()
        return out

    def get_by_chat_id(self, chat_id: int) -> List[Epic]:
        stmt = """
        SELECT id, name, description
        FROM epic
        WHERE chat_id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (chat_id,))

        epics = []
        for row in cursor.fetchall():
            epics.append(
                Epic(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    chat_id=chat_id,
                ),
            )
        cursor.close()
        return epics.copy()
