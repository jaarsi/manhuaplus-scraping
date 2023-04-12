import logging.config

import requests

from .settings import DISCORD_WH


class DiscordLoggingHandler(logging.Handler):
    def _send_discord_notification(self, message: str):
        if not (DISCORD_WH and message):
            return

        try:
            requests.post(DISCORD_WH, json={"content": message, "flags": 4})
        except Exception:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        if not record.msg:
            return

        self._send_discord_notification(self.format(record))


class CustomFormatter(logging.Formatter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, defaults={"author": "System"})
