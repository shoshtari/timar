import os

import pytest

from .config import env


def test_bool_env() -> None:
    val = env("FOO", env_type=bool, default=True)
    assert val
    os.environ["FOO"] = "false"
    val = env("FOO", env_type=bool, default=True)
    assert not val
    val = env("FOO", default=True)
    assert not val
    os.environ.pop("FOO")
    # assert raise
    with pytest.raises(ValueError):
        val = env("FOO", env_type=bool)


def test_env_int() -> None:
    val = env("FOO", env_type=int, default=1)
    assert val == 1
    os.environ["FOO"] = "5"
    val = env("FOO", env_type=int)
    assert val == 5
    val = env("FOO", default=2)
    assert val == 5
    os.environ.pop("FOO")
    val = env("FOO", default=2)
    assert val == 2
    with pytest.raises(ValueError):
        val = env("FOO", env_type=int)
