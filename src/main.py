import asyncio
import logging
import sqlite3

from telegram.ext import Application

import bot
from config import ServiceConfig
from db import initialize_repos
from log import TelegramLogger

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.ExtBot").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Updater").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
application = (
    Application.builder()
    .token(ServiceConfig.TOKEN)
    .base_url(ServiceConfig.BOT_BASE_URL)
    .build()
)

logger = TelegramLogger(
    url=f"https://tapi.bale.ai/bot{ServiceConfig.TOKEN}/sendMessage",
    chat_id=ServiceConfig.LOG_CHAT_ID,
)
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG, handlers=[logger, logging.StreamHandler()])

initialize_repos(ServiceConfig.SQLITE_FILE, ServiceConfig.MIGRATION)
bot.TimarBot(application).run(poll_interval=ServiceConfig.POLL_INTERVAL)
