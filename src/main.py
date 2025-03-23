import logging
import sqlite3

from telegram.ext import Application

import bot
from config import ServiceConfig
from db import EpicRepo, TaskRepo

logging.basicConfig(level=logging.DEBUG)
application = (
    Application.builder()
    .token(ServiceConfig.TOKEN)
    .base_url(ServiceConfig.BOT_BASE_URL)
    .build()
)


sqlitedb = sqlite3.connect(ServiceConfig.SQLITE_FILE, timeout=1)
task_repo = TaskRepo(sqlitedb=sqlitedb, do_migrate=ServiceConfig.MIGRATION)
epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=ServiceConfig.MIGRATION)

bot.TimarBot(task_repo, epic_repo, application).run()
