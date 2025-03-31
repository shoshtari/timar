import asyncio
import logging
import sqlite3

from telegram.ext import Application

import bot
from config import ServiceConfig
from db import initialize_repos

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.ExtBot").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Updater").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

application = (
    Application.builder()
    .token(ServiceConfig.TOKEN)
    .base_url(ServiceConfig.BOT_BASE_URL)
    .build()
)


initialize_repos(ServiceConfig.SQLITE_FILE, ServiceConfig.MIGRATION)
bot.TimarBot(application).run(poll_interval=ServiceConfig.POLL_INTERVAL)
