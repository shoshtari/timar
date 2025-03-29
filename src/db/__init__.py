import sqlite3

from .epic_repo import Epic, EpicRepo, IEpicRepo
from .task_repo import ITaskRepo, Task, TaskRepo
from .timelog_repo import ITimelogRepo, Timelog, TimelogRepo, TimelogStatus
from .user_state_repo import IUserStateRepo, UserState, UserStateRepo

task_repo = None
epic_repo = None
user_state_repo = None
timelog_repo = None


def initialize_repos(sqlite_file: str, do_migration: bool) -> None:
    global task_repo, epic_repo, user_state_repo, timelog_repo

    sqlitedb = sqlite3.connect(sqlite_file, timeout=1)
    task_repo = TaskRepo(sqlitedb=sqlitedb, do_migrate=do_migration)
    epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=do_migration)
    user_state_repo = UserStateRepo(sqlitedb=sqlitedb, do_migrate=do_migration)
    timelog_repo = TimelogRepo(sqlitedb=sqlitedb, do_migrate=do_migration)


__all__ = ["task_repo", "epic_repo", "user_state_repo", "timelog_repo"]
