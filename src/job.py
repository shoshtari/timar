import json
from datetime import datetime

from telegram.ext import ContextTypes

import callback_consts
import db
import message_consts


async def update_in_progress_time_logs(context: ContextTypes.DEFAULT_TYPE) -> None:
    pending_logs = db.timelog_repo.get_in_progress_logs()
    for timelog in pending_logs:
        task = db.task_repo.get_by_id(timelog.task_id)
        message_text = message_consts.TASK_TIMER_STARTED.format(
            name=task.name,
            duration=timelog.eclapsed_time,
        )
        telegram_message = json.loads(timelog.metadata)["telegram_message"]
        chat_id = telegram_message["chat"]["id"]
        message_id = telegram_message["message_id"]
        await context.bot.edit_message_text(
            text=message_text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup={
                "inline_keyboard": callback_consts.CallbackButton.aggregate(
                    [
                        callback_consts.END_TASK_TIMER.copy().add_metadata(
                            {"timelog_id": timelog.id},
                        ),
                        callback_consts.DELETE_TASK_TIMER.copy().add_metadata(
                            {"timelog_id": timelog.id},
                        ),
                    ],
                    chat_id=chat_id,
                ),
            },
        )
