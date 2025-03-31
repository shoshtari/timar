import os
from dataclasses import dataclass
from typing import Optional, Type, TypeAlias, TypeVar, cast

T = TypeVar("T")


def env(
    key: str,
    *_: tuple,
    default: Optional[T] = None,
    env_type: TypeAlias = None,
    # env_type: TypeAlias[Optional[Type[T]]] = None,
) -> T:

    if env_type is None:
        if default is not None:
            env_type = type(default)
        else:
            env_type = str
    if default is not None:
        assert type(default) == env_type
    value = os.environ.get(key)
    if value is None:
        if default is None:
            raise ValueError(f"env {key} is required")
        return default

    if env_type is bool and not isinstance(value, bool):
        return cast(T, value.lower() in ["true", "1", "yes"])
    return env_type(value)


@dataclass
class ServiceConfig:
    TOKEN: str = env("BOT_TOKEN")
    BOT_BASE_URL: str = env("BOT_BASE_URL")
    SQLITE_FILE: str = env("SQLITE", default="data.db")
    MIGRATION: bool = env("MIGRATION", default=True)
    POLL_INTERVAL: float = env("POLL_INTERVAL", default=0.2)
