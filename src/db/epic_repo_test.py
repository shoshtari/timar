import sqlite3

from .epic_repo import Epic, EpicRepo


def test_epic_repo() -> None:
    sqlitedb = sqlite3.connect(":memory:")
    epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=True)

    epic = Epic(name="test", description="test")
    epic_id = epic_repo.create(epic)
    assert epic_id > 0
    assert epic_id is not None
    assert isinstance(epic_id, int)
