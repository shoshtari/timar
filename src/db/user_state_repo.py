import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class UserState(Enum):
    NORMAL = 0
    CREATE_EPIC = 1
    CREATE_TASK = 2


class IUserStateRepo(ABC):
    @abstractmethod
    def set_state(self, user_id: int, state: UserState) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_state(self, user_id: int) -> UserState:
        raise NotImplementedError


class UserStateRepo(IUserStateRepo):
    def __init__(self, sqlitedb: sqlite3.Connection, do_migrate: bool):
        self.sqlitedb = sqlitedb
        if do_migrate:
            self.migrate()

    def migrate(self) -> None:
        stmt = """
        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY,
            state INTEGER NOT NULL
        );
        """
        self.sqlitedb.execute(stmt)

    def set_state(self, user_id: int, state: UserState) -> None:
        stmt = """
        INSERT INTO user_state(user_id, state)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET state = excluded.state
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (user_id, state.value))

    def get_state(self, user_id: int) -> UserState:
        stmt = """
        SELECT state
        FROM user_state
        WHERE user_id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (user_id,))
        row = cursor.fetchone()
        if row is None:
            return UserState.NORMAL
        return UserState(row[0])
