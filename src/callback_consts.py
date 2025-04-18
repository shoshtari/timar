import json
from typing import Any, List, Optional


class CallbackButton:

    def __init__(self, name: str, text: Optional[str] = None):
        if text is None:
            text = name
        self.__name = name
        self.__metadata: dict = {}
        self.__text = text

    @property
    def name(self) -> str:
        return self.__name

    def add_metadata(self, metadata: dict) -> "CallbackButton":
        self.__metadata |= metadata
        return self

    def set_text(self, text: str) -> "CallbackButton":
        self.__text = text
        return self

    @property
    def text(self) -> str:
        return self.__text

    def __get_callback_data(self, chat_id: int) -> str:
        return json.dumps(
            {
                "action": self.name,
                "chat_id": chat_id,
            }
            | self.__metadata,
        )

    def button(self, chat_id: int) -> dict:
        return {
            "text": self.__text,
            "callback_data": self.__get_callback_data(chat_id),
        }

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.name == other

        if isinstance(other, CallbackButton):
            return self.name == other.name

        raise NotImplementedError

    def copy(self) -> "CallbackButton":
        new_button = CallbackButton(self.__name)
        if self.__metadata:
            new_button.add_metadata(self.__metadata.copy())
        if self.__text != self.__name:
            new_button.set_text(self.__text)
        return new_button

    @staticmethod
    def aggregate(
        input_buttons: list,
        chat_id: int,
        row_limit: int = 15,
        max_count: int = 2,
    ) -> list:
        inline_buttons: List[List[dict]] = []
        last_row_remain = 0

        for button in input_buttons:
            if not isinstance(button, CallbackButton):
                raise ValueError("All buttons must be of type CallbackButton")
            but = button.button(chat_id=chat_id)
            last_row_remain -= len(button.text)
            if last_row_remain < 0 or len(inline_buttons[-1]) >= max_count:
                inline_buttons.append([])
                last_row_remain = row_limit
            inline_buttons[-1].append(but)
            last_row_remain -= len(button.text)

        return inline_buttons


TASK_MANAGEMENT = CallbackButton("مدیریت تسک ها")
EPICS_MANAGEMENT = CallbackButton("مدیریت اپیک ها")

EPIC_MENU = CallbackButton("ویرایش و یا حذف اپیک")
EDIT_EPIC = CallbackButton("ویرایش اپیک")

DELETE_EPIC = CallbackButton("حذف اپیک", text="حذف")

SELECT_EPIC_FOR_TASK = CallbackButton("انتخاب اپیک برای تسک")


RETURN_TO_MENU = CallbackButton("بازگشت به منوی اصلی")
SHOW_TASK_OPERATION_MENU = CallbackButton("ویرایش و یا حذف تسک")

EDIT_TASK = CallbackButton("ویرایش تسک")

DELETE_TASK = CallbackButton("حذف")
START_TASK_TIMER = CallbackButton("شروع تایمر")
END_TASK_TIMER = CallbackButton("پایان تایمر")
DELETE_TASK_TIMER = CallbackButton("حذف تایمر", text="حذف")

END_TASK = CallbackButton("اتمام تسک", text="اتمام")
