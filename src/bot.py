import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from telegram import Message, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import callback_consts
import job
import message_consts
from db import Epic, IEpicRepo, ITaskRepo, ITimelogRepo, IUserStateRepo, Task, UserState

logger = logging.getLogger(__name__)
import db


class TimarBot:
    def __init__(
        self,
        application: Application,
        admin_id: int,
    ):
        self.application: Application = application
        self.application.add_handler(
            MessageHandler(filters.ALL, self.handle_messages),
        )
        self.application.add_handler(
            CallbackQueryHandler(self.handle_callback),
        )
        self.admin_id = admin_id

    async def send_message(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        *_: None,
        chat_id: int,
        text: str,
        reply_markup: Optional[dict] = None,
    ) -> Message:
        default_markup = {"keyboard": [["منوی اصلی"]]}
        if reply_markup is None:
            reply_markup = {}
        if "inline_keyboard" not in reply_markup:
            reply_markup["inline_keyboard"] = callback_consts.CallbackButton.aggregate(
                [callback_consts.RETURN_TO_MENU],
                chat_id,
            )

        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=default_markup,
        )
        await message.delete()
        return await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def handle_start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:

        chat_id = update.effective_chat.id
        reply_markup = {
            "inline_keyboard": [
                [
                    callback_consts.TASK_MANAGEMENT.button(chat_id),
                    callback_consts.EPICS_MANAGEMENT.button(chat_id),
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
        user_epics = db.epic_repo.get_by_chat_id(chat_id)

        if user_epics:
            text = message_consts.MANAGE_EPIC_MESSAGE

            buttons = []
            for epic in user_epics:
                button = callback_consts.EPIC_MENU.copy()
                button.add_metadata({"epic_id": epic.id})
                button.set_text(epic.name)
                buttons.append(button)

            reply_markup = {
                "inline_keyboard": callback_consts.CallbackButton.aggregate(
                    buttons,
                    update.effective_chat.id,
                ),
            }
        else:
            text = message_consts.MANAGE_EPIC_EMPTY_MESSAGE
            reply_markup = None

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
        db.user_state_repo.set_state(chat_id, UserState.CREATE_EPIC)
        await self.send_message(
            context,
            chat_id=chat_id,
            text=text,
        )

    async def handle_report_initiate(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.effective_chat.id
        db.user_state_repo.set_state(
            chat_id,
            UserState.REPORT_DURATION,
        )
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.REPORT_GET_DURATION,
        )

    async def handle_report_duration(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.effective_chat.id
        db.user_state_repo.set_state(chat_id, UserState.NORMAL)
        duration = timedelta(days=float(update.message.text))

    async def handle_task_management(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        chat_id = update.effective_chat.id
        tasks = db.task_repo.get_by_chat_id(chat_id)
        if not tasks:
            await self.send_message(
                context,
                chat_id=chat_id,
                text=message_consts.MANAGE_TASK_EMPTY_MESSAGE,
            )
            return
        buttons = []
        for task in tasks:
            button = callback_consts.SHOW_TASK_OPERATION_MENU.copy()
            button.add_metadata({"task_id": task.id})
            button.set_text(task.name)
            buttons.append(button)
        buttons = callback_consts.CallbackButton.aggregate(buttons, chat_id=chat_id)
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

        db.epic_repo.create(
            Epic(name=title, description=description, chat_id=chat_id),
        )
        db.user_state_repo.set_state(chat_id, UserState.NORMAL)
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

        user_epics = db.epic_repo.get_by_chat_id(chat_id)
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
        db.user_state_repo.set_state(
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
        metadata = db.user_state_repo.get_state_and_metadata(chat_id)[1]

        title = text[0].strip()
        description = "\n".join(text[1:]).strip()
        chat_id = update.message.chat.id
        epic_id = metadata["epic_id"]
        db.task_repo.create(
            Task(name=title, description=description, epic_id=epic_id),
        )
        db.user_state_repo.set_state(chat_id, UserState.NORMAL)
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.NEW_TASK_CREATED.format(name=title),
        )

    async def handle_epic_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback_data: dict,
    ) -> None:
        chat_id = update.effective_chat.id
        epic_id = callback_data["epic_id"]
        epic = db.epic_repo.get_by_id(epic_id)
        text = message_consts.EDIT_EPIC.format(
            name=epic.name,
            description=epic.description,
        )
        buttons = callback_consts.CallbackButton.aggregate(
            [
                callback_consts.EDIT_EPIC.copy()
                .set_text("ویرایش نام")
                .add_metadata(
                    {"epic_id": epic_id, "column": "name"},
                ),
                callback_consts.EDIT_EPIC.copy()
                .set_text("ویرایش توضیحات")
                .add_metadata(
                    {"epic_id": epic_id, "column": "description"},
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

    async def handle_task_operation_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback_data: dict,
    ) -> None:
        chat_id = update.effective_chat.id
        task_id = callback_data["task_id"]
        task = db.task_repo.get_by_id(task_id)
        text = message_consts.TASK_OPERATION_MENU.format(
            name=task.name,
            description=task.description,
        )
        metadata = {"task_id": task.id, "task_name": task.name}

        buttons = callback_consts.CallbackButton.aggregate(
            [
                callback_consts.EDIT_TASK.copy()
                .set_text("تغییر نام")
                .add_metadata(
                    metadata=metadata | {"column": "name"},
                ),
                callback_consts.EDIT_TASK.copy()
                .set_text("ویرایش توضیحات")
                .add_metadata(
                    metadata=metadata | {"column": "description"},
                ),
                callback_consts.DELETE_TASK.copy().add_metadata(metadata=metadata),
                callback_consts.START_TASK_TIMER.copy().add_metadata(metadata=metadata),
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

    async def handle_delete_epic(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        epic_id: int,
    ) -> None:
        epic = db.epic_repo.get_by_id(epic_id)
        if epic.chat_id != update.effective_chat.id:
            logger.warning(
                f"User {update.effective_chat.id} tried to delete epic {epic_id} which is not theirs",
            )
            return
        db.epic_repo.delete(epic_id)
        await self.send_message(
            context,
            chat_id=update.effective_chat.id,
            text=message_consts.EPIC_DELETED.format(name=epic.name),
        )

    async def handle_delete_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        task_id: int,
        task_name: str,
    ) -> None:
        given_chat_id = update.effective_chat.id
        task_chat_id = db.task_repo.get_owner_chat(task_id)
        if task_chat_id != task_chat_id:
            logger.warning(
                f"User {given_chat_id} tried to delete task {task_id} that doesn't belong to them",
            )
            await self.send_message(
                context,
                chat_id=given_chat_id,
                text=message_consts.UNAUTHORIZED,
            )

        db.task_repo.delete(task_id)
        await self.send_message(
            context,
            chat_id=given_chat_id,
            text=message_consts.TASK_DELETED.format(name=task_name),
        )

    async def handle_edit_task(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        task_id: int,
        column: str,
    ) -> None:
        chat_id = update.effective_chat.id
        db.user_state_repo.set_state(
            chat_id,
            UserState.EDIT_TASK,
            metadata={"column": column, "task_id": task_id},
        )
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.GET_INPUT_FOR_TASK_EDIT,
        )

    async def handle_edit_task_state(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        value = update.message.text
        _, metadata = db.user_state_repo.get_state_and_metadata(
            update.effective_chat.id,
        )
        task_id = metadata["task_id"]
        column = metadata["column"]

        db.task_repo.edit(task_id, column, value)
        await self.send_message(
            context,
            chat_id=update.effective_chat.id,
            text=message_consts.TASK_EDITED,
        )

    async def handle_start_task_timer(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback_data: Optional[dict] = None,
    ) -> None:
        if callback_data is None:
            callback_data = json.loads(update.callback_query.data)
        task_id = callback_data["task_id"]
        task_name = callback_data["task_name"]
        start_time = datetime.now()
        timelog_id = db.timelog_repo.create(task_id, start_time)
        buttons = [
            callback_consts.END_TASK_TIMER.copy().add_metadata(
                {
                    "timelog_id": timelog_id,
                    "task_id": task_id,
                },
            ),
            callback_consts.DELETE_TASK_TIMER.copy().add_metadata(
                {
                    "timelog_id": timelog_id,
                },
            ),
        ]

        reply_markup = {
            "inline_keyboard": callback_consts.CallbackButton.aggregate(
                buttons,
                update.effective_chat.id,
            ),
        }
        res = await self.send_message(
            context,
            chat_id=update.effective_chat.id,
            text=message_consts.TASK_TIMER_STARTED.format(
                name=task_name,
                duration="۰ ثانیه",
            ),
            reply_markup=reply_markup,
        )

        metadata = {"telegram_message": res.to_dict()}
        db.timelog_repo.set_metadata(
            timelog_id=timelog_id,
            metadata=json.dumps(metadata),
        )

    async def handle_end_task_timer(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        data: dict,
    ) -> None:
        end_time = datetime.now()
        db.timelog_repo.set_end_if_not_exists(data["timelog_id"], end_time)
        timelog = db.timelog_repo.get_by_id(data["timelog_id"])
        task = db.task_repo.get_by_id(timelog.task_id)
        chat_id = json.loads(timelog.metadata)["telegram_message"]["chat"]["id"]

        reply_markup = {
            "inline_keyboard": callback_consts.CallbackButton.aggregate(
                [callback_consts.RETURN_TO_MENU],
                chat_id=chat_id,
            ),
        }
        res = await self.send_message(
            context,
            chat_id=update.effective_chat.id,
            text=message_consts.TASK_TIMER_ENDED.format(
                name=task.name,
                duration=timelog.eclapsed_time,
            ),
            reply_markup=reply_markup,
        )

    async def handle_delete_task_timer(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        timelog_id: int,
    ) -> None:
        db.timelog_repo.delete(timelog_id=timelog_id)
        await self.send_message(
            context=context,
            chat_id=chat_id,
            text=message_consts.TIMELOG_DELETED,
        )

    async def handle_edit_epic_button(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        epic_id: int,
        column: str,
    ) -> None:
        state_metadata = {
            "epic_id": epic_id,
            "column": column,
        }
        db.user_state_repo.set_state(
            chat_id,
            UserState.EDIT_EPIC,
            metadata=state_metadata,
        )
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.GET_INPUT_FOR_EPIC_EDIT,
        )

    async def handle_edit_epic_with_input(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        value: str,
    ) -> None:
        user_state, metadata = db.user_state_repo.get_state_and_metadata(chat_id)
        epic_id = metadata["epic_id"]
        column = metadata["column"]
        db.epic_repo.edit(epic_id, column, value)
        await self.send_message(
            context,
            chat_id=chat_id,
            text=message_consts.EPIC_EDITED,
        )

    async def handle_state(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        user_state = db.user_state_repo.get_state(update.effective_chat.id)
        match user_state:
            case UserState.CREATE_EPIC:
                await self.handle_create_epic(update, context)
            case UserState.CREATE_TASK:
                await self.handle_create_task(update, context)
            case UserState.EDIT_TASK:
                await self.handle_edit_task_state(update, context)
            case UserState.EDIT_EPIC:
                await self.handle_edit_epic_with_input(
                    context,
                    update.effective_chat.id,
                    update.message.text,
                )
            case _:
                logger.warning(
                    f"unknown message {update.message.text}, user state: {user_state}",
                )

    async def handle_messages(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        match update.message.text:
            case "/start" | "منوی اصلی":
                await self.handle_start_command(update, context)
            case "/new_epic":
                await self.handle_new_epic(update, context)
            case "/new_task":
                await self.handle_new_task(update, context)
            case "/shutdown":
                if update.effective_chat.id != self.admin_id:
                    logger.warning(f"unauthorized shutdown {update.effective_chat.id}")
                    return
                await update.message.reply_text("در حال خاموش کردن بات")
                self.application.stop_running()
                await self.application.stop()
                await self.application.shutdown()
            case _:
                await self.handle_state(update, context)
                return

    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        logger.debug("new callback query recieved")
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
            case callback_consts.EPIC_MENU:
                await self.handle_epic_menu(update, context, data)
            case callback_consts.EDIT_EPIC:
                await self.handle_edit_epic_button(
                    context,
                    update.effective_chat.id,
                    data["epic_id"],
                    data["column"],
                )
            case callback_consts.SHOW_TASK_OPERATION_MENU:
                await self.handle_task_operation_menu(update, context, data)
            case callback_consts.DELETE_TASK:
                await self.handle_delete_task(
                    update,
                    context,
                    data["task_id"],
                    data["task_name"],
                )
            case callback_consts.EDIT_TASK:
                await self.handle_edit_task(
                    update,
                    context,
                    data["task_id"],
                    data["column"],
                )

            case callback_consts.RETURN_TO_MENU:
                await self.handle_start_command(update, context)
            case callback_consts.DELETE_EPIC:
                epic_id = data["epic_id"]
                await self.handle_delete_epic(update, context, epic_id)
            case callback_consts.START_TASK_TIMER:
                await self.handle_start_task_timer(update, context, data)

            case callback_consts.END_TASK_TIMER:
                await self.handle_end_task_timer(update, context, data)
            case callback_consts.DELETE_TASK_TIMER:
                await self.handle_delete_task_timer(
                    context,
                    update.effective_chat.id,
                    data["timelog_id "],
                )
            case callback_consts.EDIT_EPIC:
                await self.handle_edit_epic_button(
                    context,
                    update.effective_chat.id,
                    data["epic_id"],
                    data["column"],
                )

            case _:
                logger.warning(f"Unknown action {data['action']}")

    def run(self, poll_interval: float) -> None:

        self.application.job_queue.run_repeating(
            job.update_in_progress_time_logs,
            interval=1,
            first=0,
        )
        self.application.run_polling(poll_interval=poll_interval)
