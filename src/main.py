import sqlite3

from telegram.ext import Application

import config
from config import ServiceConfig as config
from db import EpicRepo, TaskRepo

application = (
    Application.builder().token(config.TOKEN).base_url(config.BOT_BASE_URL).build()
)

sqlitedb = sqlite3.connect(config.SQLITE_FILE, timeout=1)
task_repo = TaskRepo(sqlitedb=sqlitedb, do_migrate=config.MIGRATION)
epic_repo = EpicRepo(sqlitedb=sqlitedb, do_migrate=config.MIGRATION)
