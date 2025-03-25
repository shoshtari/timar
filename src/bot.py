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
import message_consts
from db import Epic, IEpicRepo, ITaskRepo, IUserStateRepo, Task, UserState

logger = logging.getLogger(__name__)


class TimarBot:
    def __init__(
        self,
        epic_repo: IEpicRepo,
        task_repo: ITaskRepo,
        user_state_repo: IUserStateRepo,
        application: Application,
    ):
        self.epic_repo = epic_repo
        self.task_repo = task_repo
        self.user_state_repo = user_state_repo
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
                    callback_consts.EPICS_MANAGEMENT.button(chat_id),
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

        if user_epics:
            text = message_consts.MANAGE_EPIC_MESSAGE
        else:
            text = message_consts.MANAGE_EPIC_EMPTY_MESSAGE

        buttons = []
        for epic in user_epics:
            button = callback_consts.EDIT_EPIC.copy()
            button.add_metadata({"epic_id": epic.id})
            button.set_text(epic.name)
            buttons.append(button)

        reply_markup = {
            "inline_keyboard": callback_consts.CallbackButton.aggregate(
                buttons,
                update.effective_chat.id,
            ),
        }

        await self.send_message(
            context,
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def handle_new_epic(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.message.chat.id
        text = message_consts.NEW_EPIC_MESSAGE
        self.user_state_repo.set_state(chat_id, UserState.CREATE_EPIC)
        await self.send_message(
            context,
            chat_id=chat_id,
            text=text,
        )

    async def handle_task_management(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.effective_chat.id
        tasks = self.task_repo.get_by_chat_id(chat_id)
        if not tasks:
            await self.send_message(
                context,
                chat_id=chat_id,
                text=message_consts.MANAGE_TASK_EMPTY_MESSAGE,
            )
        buttons = []
        for task in tasks:
            button = callback_consts.EDIT_TASK.copy()
            button.add_metadata({"task_id": task.id})
            button.set_text(task.name)
            buttons.append(button)
        buttons = callback_consts.CallbackButton.aggregate(buttons)
        reply_markup = {"inline_keyboard": buttons}
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.MANAGE_TASK_MESSAGE,
            reply_markup=reply_markup,
        )

    async def handle_create_epic(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        text = update.message.text.split("\n")
        title = text[0].strip()

        if len(text) > 1:
            description = "\n".join(text[1:]).strip()
        else:
            description = ""
        chat_id = update.message.chat.id

        self.epic_repo.create(
            Epic(name=title, description=description, chat_id=chat_id),
        )
        self.user_state_repo.set_state(chat_id, UserState.NORMAL)
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.NEW_EPIC_CREATED.format(name=title),
        )

    async def handle_new_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.message.chat.id
        text = update.message.text.split("\n")
        title = text[0].strip()

        user_epics = self.epic_repo.get_by_chat_id(chat_id)
        if not user_epics:
            await self.send_message(
                context,
                chat_id=chat_id,
                text=message_consts.NO_EPIC_MESSAGE,
            )
            return

        buttons = []
        for epic in user_epics:
            button = callback_consts.SELECT_EPIC_FOR_TASK.copy()
            button.add_metadata({"epic_id": epic.id})
            button.set_text(epic.name)
            buttons.append(button)

        reply_markup = {
            "inline_keyboard": callback_consts.CallbackButton.aggregate(
                buttons,
                chat_id,
            ),
        }
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.SELECT_EPIC_FOR_NEW_TASK,
            reply_markup=reply_markup,
        )

    async def handle_selected_epic_for_new_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback_data: dict,
    ) -> None:
        # should go to set title and description
        self.user_state_repo.set_state(
            update.effective_chat.id,
            UserState.CREATE_TASK,
            metadata={"epic_id": callback_data["epic_id"]},
        )
        await self.send_message(
            context,
            chat_id=update.effective_chat.id,
            text=message_consts.SEND_TASK_TITLE_AND_DESCRIPTION,
        )

    async def handle_create_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        text = update.message.text.split("\n")
        chat_id = update.effective_chat.id
        metadata = self.user_state_repo.get_state_and_metadata(chat_id)[1]

        title = text[0].strip()
        description = "\n".join(text[1:]).strip()
        chat_id = update.message.chat.id
        epic_id = metadata["epic_id"]
        self.task_repo.create(
            Task(name=title, description=description, epic_id=epic_id),
        )
        self.user_state_repo.set_state(chat_id, UserState.NORMAL)
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.NEW_TASK_CREATED.format(name=title),
        )

    async def handle_edit_epic(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback_data: dict,
    ) -> None:
        chat_id = update.effective_chat.id
        epic_id = callback_data["epic_id"]
        epic = self.epic_repo.get_by_id(epic_id)
        text = message_consts.EDIT_EPIC.format(
            name=epic.name,
            description=epic.description,
        )
        buttons = callback_consts.CallbackButton.aggregate(
            [
                callback_consts.EDIT_EPIC_NAME.copy().add_metadata(
                    {"epic_id": epic_id},
                ),
                callback_consts.EDIT_EPIC_DESCRIPTION.copy().add_metadata(
                    {"epic_id": epic_id},
                ),
                callback_consts.DELETE_EPIC.copy().add_metadata({"epic_id": epic_id}),
            ],
            chat_id,
        )
        reply_markup = {"inline_keyboard": buttons}
        await self.send_message(
            context,
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def handle_edit_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback_data: dict,
    ) -> None:
        chat_id = update.effective_chat.id
        task_id = callback_data["task_id"]
        task = self.task_repo.get_by_id(task_id)
        text = message_consts.EDIT_TASK.format(
            name=task.name,
            description=task.description,
        )
        buttons = callback_consts.CallbackButton.aggregate(
            [
                callback_consts.EDIT_TASK_NAME.copy().add_metadata(
                    {"task_id": task_id},
                ),
                callback_consts.EDIT_TASK_DESCRIPTION.copy().add_metadata(
                    {"task_id": task_id},
                ),
                callback_consts.DELETE_TASK.copy().add_metadata({"task_id": task_id}),
                callback_consts.TASK_TIMER.copy().add_metadata({"task_id": task_id}),
            ],
            chat_id,
        )
        reply_markup = {"inline_keyboard": buttons}
        await self.send_message(
            context,
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def handle_state(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        user_state = self.user_state_repo.get_state(update.message.chat.id)
        match user_state:
            case UserState.CREATE_EPIC:
                await self.handle_create_epic(update, context)
            case UserState.CREATE_TASK:
                await self.handle_create_task(update, context)
            case UserState.NORMAL:
                logger.warning(f"unknown message {update.message.text}")

    async def handle_messages(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        match update.message.text:
            case "/start":
                await self.handle_start_command(update, context)
            case "/new_epic":
                await self.handle_new_epic(update, context)
            case "/new_task":
                await self.handle_new_task(update, context)
            case _:
                await self.handle_state(update, context)

    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        query = update.callback_query
        try:
            data = json.loads(query.data)
        except Exception as error:
            logger.error(f"Error parsing callback data: {error =}, {query.data}")
        match data["action"]:
            case callback_consts.EPICS_MANAGEMENT:
                await self.handle_epic_management(update, context)
            case callback_consts.TASK_MANAGEMENT:
                await self.handle_task_management(update, context)
            case callback_consts.SELECT_EPIC_FOR_TASK:
                await self.handle_selected_epic_for_new_task(update, context, data)
            case callback_consts.EDIT_EPIC:
                await self.handle_edit_epic(update, context, data)
            case callback_consts.EDIT_TASK:
                await self.handle_edit_task(update, context, data)

            case _:
                logger.warning(f"Unknown action {data['action']}")

    def run(self) -> None:
        self.application.add_handler(
            MessageHandler(filters.ALL, self.handle_messages),
        )
        self.application.add_handler(
            CallbackQueryHandler(self.handle_callback),
        )
        self.application.run_polling()
