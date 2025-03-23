import sqlite3

from .epic_repo import Epic, EpicRepo


def test_epic_repo() -> None:
    sqlitedb = sqlite3.connect(":memory:")
    epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=True)

    epic = Epic(name="test", description="test", chat_id=2)
    epic_id = epic_repo.create(epic)
    assert epic_id > 0
    assert epic_id is not None
    assert isinstance(epic_id, int)

    epics = epic_repo.get_by_chat_id(3)
    assert len(epics) == 0

    epics = epic_repo.get_by_chat_id(2)
    assert len(epics) == 1
    assert epics[0].id == epic_id
    assert epics[0].name == epic.name
    assert epics[0].description == epic.description
    assert epics[0].chat_id == epic.chat_id
