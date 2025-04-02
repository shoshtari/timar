import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class UserState(Enum):
    NORMAL = 0
    CREATE_EPIC = 1
    CREATE_TASK = 2
    EDIT_TASK = 3
    REPORT_DURATION = 4
    EDIT_EPIC = 5


class IUserStateRepo(ABC):
    @abstractmethod
    def set_state(
        self,
        user_id: int,
        state: UserState,
        metadata: Optional[dict] = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_state(self, user_id: int) -> UserState:
        raise NotImplementedError

    @abstractmethod
    def get_state_and_metadata(self, user_id: int) -> Tuple[UserState, dict]:
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
            state INTEGER NOT NULL,
            metadata TEXT DEFAULT NULL
        );
        """
        self.sqlitedb.execute(stmt)
        self.sqlitedb.commit()

    def set_state(
        self,
        user_id: int,
        state: UserState,
        metadata: Optional[dict] = None,
    ) -> None:
        stmt = """
        INSERT INTO user_state(user_id, state, metadata)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET state = excluded.state , metadata = excluded.metadata
        """
        cursor = self.sqlitedb.cursor()
        metadata_str = json.dumps(metadata) if metadata else None
        cursor.execute(stmt, (user_id, state.value, metadata_str))

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

    def get_state_and_metadata(self, user_id: int) -> Tuple[UserState, dict]:
        stmt = """
        SELECT state, metadata
        FROM user_state
        WHERE user_id = ?
        """
        cursor = self.sqlitedb.cursor()
        cursor.execute(stmt, (user_id,))
        row = cursor.fetchone()
        if row is None:
            return UserState.NORMAL, {}
        user_state = UserState(row[0])
        metadata = json.loads(row[1]) if row[1] else {}
        return user_state, metadata
