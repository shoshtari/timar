import logging
import sqlite3

from telegram.ext import Application

import bot
from config import ServiceConfig
from db import EpicRepo, TaskRepo, UserStateRepo

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.ExtBot").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Updater").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

application = (
    Application.builder()
    .token(ServiceConfig.TOKEN)
    .base_url(ServiceConfig.BOT_BASE_URL)
    .build()
)


sqlitedb = sqlite3.connect(ServiceConfig.SQLITE_FILE, timeout=1)
task_repo = TaskRepo(sqlitedb=sqlitedb, do_migrate=ServiceConfig.MIGRATION)
epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=ServiceConfig.MIGRATION)
user_state_repo = UserStateRepo(sqlitedb=sqlitedb, do_migrate=ServiceConfig.MIGRATION)

bot.TimarBot(task_repo, epic_repo, application).run()
