import sqlite3
from typing import Generator

import pytest

from .epic_repo import Epic, EpicRepo


@pytest.fixture
def repo() -> Generator[EpicRepo]:
    conn = sqlite3.connect(":memory:")
    repo = EpicRepo(conn, do_migrate=True)
    yield repo
    conn.close()


def test_create_and_fetch_epic(repo: EpicRepo) -> None:
    epic = Epic(name="Test Epic", description="Test Description", chat_id=123)
    epic_id = repo.create(epic)

    retrieved_epic = repo.get_by_id(epic_id)
    assert retrieved_epic.id == epic_id
    assert retrieved_epic.name == epic.name
    assert retrieved_epic.description == epic.description
    assert retrieved_epic.chat_id == epic.chat_id


def test_delete_logic(repo: EpicRepo) -> None:
    epic = Epic(name="Test Epic", description="Test Description", chat_id=123)
    epic_id = repo.create(epic)

    retrieved_epic = repo.get_by_id(epic_id)
    assert retrieved_epic is not None

    repo.delete(epic_id)

    with pytest.raises(ValueError):
        repo.get_by_id(epic_id)

    epics = repo.get_by_chat_id(123)
    assert epic_id not in [e.id for e in epics]
