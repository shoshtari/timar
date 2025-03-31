import sqlite3
from datetime import datetime, timedelta
from typing import Generator

import pytest

from . import Epic, IEpicRepo, ITaskRepo, Task, initialize_repos
from .timelog_repo import ITimelogRepo, TimelogRepo, TimelogStatus


@pytest.fixture
def timelog_repo() -> Generator[ITimelogRepo, None, None]:
    initialize_repos(":memory:", do_migration=True)
    from . import timelog_repo

    if timelog_repo is None:
        raise ValueError("timelog_repo is not initialized")
    yield timelog_repo


@pytest.fixture
def task_repo() -> Generator[ITaskRepo, None, None]:
    initialize_repos(":memory:", do_migration=True)
    from . import task_repo

    if task_repo is None:
        raise ValueError("task_repo is not initialized")

    yield task_repo


@pytest.fixture
def epic_repo() -> Generator[IEpicRepo, None, None]:
    initialize_repos(":memory:", do_migration=True)
    from . import epic_repo

    if epic_repo is None:
        raise ValueError("epic repo is none")

    yield epic_repo


def test_create_timelog(timelog_repo: ITimelogRepo) -> None:
    task_id = 1
    start_time = datetime.now()
    timelog_id = timelog_repo.create(task_id, start_time)
    assert timelog_id > 0

    timelog = timelog_repo.get_by_id(timelog_id)
    assert timelog.task_id == task_id
    assert timelog.start == start_time
    assert timelog.status == TimelogStatus.IN_PROGRESS.name


def test_set_metadata(timelog_repo: ITimelogRepo) -> None:
    task_id = 1
    start_time = datetime.now()
    timelog_id = timelog_repo.create(task_id, start_time)

    metadata = "Test metadata"
    timelog_repo.set_metadata(timelog_id, metadata)

    timelog = timelog_repo.get_by_id(timelog_id)
    assert timelog.metadata == metadata


def test_get_in_progress_logs(timelog_repo: ITimelogRepo) -> None:
    task_id = 1
    start_time = datetime.now()
    timelog_repo.create(task_id, start_time)

    in_progress_logs = timelog_repo.get_in_progress_logs()
    assert len(in_progress_logs) == 1
    assert in_progress_logs[0].task_id == task_id
    assert in_progress_logs[0].status == TimelogStatus.IN_PROGRESS.name


def test_set_end_if_not_exists(timelog_repo: ITimelogRepo) -> None:
    task_id = 1
    start_time = datetime.now()
    timelog_id = timelog_repo.create(task_id, start_time)

    end_time = datetime.now()
    timelog_repo.set_end_if_not_exists(timelog_id, end_time)

    timelog = timelog_repo.get_by_id(timelog_id)
    assert timelog.end == end_time
    assert timelog.status == TimelogStatus.DONE.name


def test_get_by_user_id_and_time(
    timelog_repo: ITimelogRepo,
    epic_repo: IEpicRepo,
    task_repo: ITaskRepo,
) -> None:
    user_id = 1
    start_time = datetime.now()
    duration = timedelta(days=1)

    epic_id = epic_repo.create(Epic(name="foo", description="foo2", chat_id=user_id))
    task_id = task_repo.create(Task(epic_id=epic_id, description="bar2", name="bar"))

    timelog_repo.create(task_id, start_time)

    timelogs = timelog_repo.get_by_user_id_and_time(user_id, duration)
    assert len(timelogs) == 1
    assert timelogs[0].task_id == task_id
    assert timelogs[0].start == start_time
