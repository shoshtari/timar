import sqlite3
import zoneinfo
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
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

    @abstractmethod
    def get_by_id(self, epic_id: int) -> Epic:
        raise NotImplementedError

    @abstractmethod
    def get_by_chat_id(self, chat_id: int) -> List[Epic]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, epic_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def edit(self, epic_id: int, column: str, value: str) -> None:
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
            description TEXT NOT NULL,
            deleted_at TIMESTAMP DEFAULT NULL
        );
        """
        self.sqlitedb.execute(stmt)
        self.sqlitedb.commit()

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
        WHERE chat_id = ? AND deleted_at IS NULL
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

    def get_by_id(self, epic_id: int) -> Epic:
        stmt = """
        SELECT chat_id, name, description
        FROM epic
        WHERE id = ? AND deleted_at IS NULL
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (epic_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"epic with id {epic_id} not found")
        return Epic(
            id=epic_id,
            chat_id=row[0],
            name=row[1],
            description=row[2],
        )

    def delete(self, epic_id: int) -> None:
        stmt = """
        UPDATE epic
        SET deleted_at = ?
        WHERE id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(
            stmt,
            (datetime.now(zoneinfo.ZoneInfo("Asia/Tehran")).isoformat(), epic_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"epic with id {epic_id} not found or already deleted")
        self.sqlitedb.commit()

    def edit(self, epic_id: int, column: str, value: str) -> None:
        assert column in ("name", "description"), column

        stmt = f"""
        UPDATE epic
        SET {column} = ?
        WHERE id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (value, epic_id))
        if cursor.rowcount == 0:
            raise ValueError(f"epic with id {epic_id} not found")
        self.sqlitedb.commit()
