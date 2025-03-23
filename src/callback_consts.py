import json
from typing import Any


class CallbackButton:

    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

    def __get_callback_data(self, chat_id: int, metadata: dict) -> str:
        return json.dumps(
            {
                "action": self.name,
                "chat_id": chat_id,
            }
            | metadata,
        )

    def button(self, chat_id: int) -> dict:
        return {
            "text": self.__name,
            "callback_data": self.__get_callback_data(chat_id, {}),
        }

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CallbackButton):
            return False
        return self.name == other.name


TASK_MANAGEMENT = CallbackButton("مدیریت تسک ها")
EPIC_MANAGEMENT = CallbackButton("مدیریت اپیک ها")
