import sqlite3

from .epic_repo import Epic, EpicRepo
from .task_repo import Task, TaskRepo


def test_epic_repo() -> None:
    sqlitedb = sqlite3.connect(":memory:")
    task_repo = TaskRepo(sqlitedb=sqlitedb, do_migrate=True)
    epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=True)

    epic_id = epic_repo.create(Epic(name="test", description="test"))
    task = Task(name="test", description="test", epic_id=epic_id)

    task_id = task_repo.create(task)
    assert task_id > 0
    assert task_id is not None
    assert isinstance(task_id, int)
