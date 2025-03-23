import json
import logging
from typing import Optional

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import callback_consts
from db import Epic, IEpicRepo, ITaskRepo, Task


class TimarBot:
    def __init__(
        self,
        epic_repo: IEpicRepo,
        task_repo: ITaskRepo,
        application: Application,
    ):
        self.epic_repo = epic_repo
        self.task_repo = task_repo
        self.application: Application = application

    async def send_message(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        *_: None,
        chat_id: int,
        text: str,
        reply_markup: Optional[dict] = None,
    ) -> None:
        if reply_markup is None:
            reply_markup = {}
        # if "reply_keyboard" not in reply_markup:
        #     reply_markup["reply_keyboard"] = ReplyKeyboardMarkup([["S"]])

        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def handle_start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:

        chat_id = update.message.chat.id
        reply_markup = {
            "inline_keyboard": [
                [
                    callback_consts.EPIC_MANAGEMENT.button(chat_id),
                    callback_consts.TASK_MANAGEMENT.button(chat_id),
                ],
            ],
        }

        await self.send_message(
            context,
            chat_id=update.effective_chat.id,
            text="به تیمار خوش آمدید",
            reply_markup=reply_markup,
        )

    async def handle_epic_management(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.callback_query.message.chat.id
        user_epics = self.epic_repo.get_by_chat_id(chat_id)
        reply_markup = {
            "inline_keyboard": [
                [
                    callback_consts.CREATE_EPIC.button(chat_id),
                    callback_consts.LIST_EPIC.button(chat_id),
                ],
            ],
        }
        await self.send_message(
            context,
            chat_id=chat_id,
            text="مدیریت اپیک",
            reply_markup=reply_markup,
        )

    async def handle_task_management(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        raise NotImplementedError

    async def handle_messages(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        match update.message.text:
            case "/start":
                await self.handle_start_command(update, context)

    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        query = update.callback_query
        data = json.loads(query.data)
        match data["action"]:
            case callback_consts.EPIC_MANAGEMENT:
                await self.handle_epic_management(update, context)
            case callback_consts.TASK_MANAGEMENT:
                await self.handle_task_management(update, context)

    def run(self) -> None:
        self.application.add_handler(
            MessageHandler(filters.ALL, self.handle_messages),
        )
        self.application.add_handler(
            CallbackQueryHandler(self.handle_callback),
        )
        self.application.run_polling()
