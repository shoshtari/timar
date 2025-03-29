import sqlite3
from typing import Generator

import pytest

from .timelog_repo import ITimelogRepo, TimelogRepo


@pytest.fixture
def repo() -> Generator[ITimelogRepo, None, None]:
    conn = sqlite3.connect(":memory:")
    repo = TimelogRepo(conn, do_migrate=True)
    yield repo
    conn.close()


def test_timelog_repo(repo: ITimelogRepo) -> None:
    pass
