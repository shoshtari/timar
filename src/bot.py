import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from db import Epic, IEpicRepo, ITaskRepo, Task

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.ExtBot").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Updater").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)


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

    async def handle_start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        await update.message.reply_text(
            "Hello! I am TimarBot. I am here to help you manage your tasks and epics.",
        )

    def run(self) -> None:
        self.application.add_handler(CommandHandler("start", self.handle_start_command))
        self.application.add_handler(
            MessageHandler(filters.ALL, self.handle_start_command),
        )
        self.application.run_polling()
