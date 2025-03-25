import sqlite3

from .user_state_repo import UserState, UserStateRepo


def test_epic_repo() -> None:
    sqlitedb = sqlite3.connect(":memory:")
    user_state_repo = UserStateRepo(sqlitedb=sqlitedb, do_migrate=True)

    user_id = 1

    user_state_repo.set_state(user_id, UserState.NORMAL)
    assert user_state_repo.get_state(user_id) == UserState.NORMAL

    user_state_repo.set_state(user_id, UserState.CREATE_EPIC)
    assert user_state_repo.get_state(user_id) == UserState.CREATE_EPIC

    # test metadata
    metadata = {"foo": "bar"}
    user_state_repo.set_state(user_id, UserState.CREATE_TASK, metadata)
    state, metadata = user_state_repo.get_state_and_metadata(user_id)
    assert state == UserState.CREATE_TASK
    assert metadata == {"foo": "bar"}
