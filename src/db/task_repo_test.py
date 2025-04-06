import sqlite3

from .epic_repo import Epic, EpicRepo
from .task_repo import Task, TaskRepo


def test_task_repo() -> None:
    sqlitedb = sqlite3.connect(":memory:")
    task_repo = TaskRepo(sqlitedb=sqlitedb, do_migrate=True)
    epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=True)

    epic_id = epic_repo.create(Epic(name="test", description="test", chat_id=1))
    task = Task(name="test", description="test", epic_id=epic_id)

    task_id = task_repo.create(task)
    assert task_id > 0
    assert task_id is not None
    assert isinstance(task_id, int)

    tasks = task_repo.get_undone_by_chat_id(1)
    assert len(tasks) == 1
    assert tasks[0].id == task_id
    assert tasks[0].name == "test"
    assert tasks[0].description == "test"
    assert tasks[0].epic_id == epic_id
