import asyncio
import json
import logging
from datetime import datetime

import requests
import telegram
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class TelegramLogger(logging.Handler):
    def __init__(self, url: str, chat_id: int):

        self.url = url
        self.chat_id = chat_id

        MAX_POOLSIZE = 100
        self.session = session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json",
            },
        )
        self.session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=5,
                    backoff_factor=0.5,
                    status_forcelist=[403, 500],
                ),
                pool_connections=MAX_POOLSIZE,
                pool_maxsize=MAX_POOLSIZE,
            ),
        )
        super().__init__()

    def format(self, entry: logging.LogRecord) -> str:
        message = json.dumps(
            {
                "time": datetime.fromtimestamp(entry.created).isoformat(),
                "pathname": entry.pathname,
                "lineno": entry.lineno,
                "level": entry.levelname,
                "message": entry.msg,
                "name": entry.name,
            },
            indent=4,
            sort_keys=True,
        )
        message = f"```\n{message}\n```".strip()
        return message

    def emit(self, record: logging.LogRecord) -> None:
        if record.name == "urllib3.connectionpool":
            return  # it cause infinite recursion

        body = json.dumps({"chat_id": self.chat_id, "text": self.format(record)})
        res = self.session.post(
            url=self.url,
            data=body,
            headers={"Content-Type": "Application/Json"},
        )
        res.raise_for_status()
