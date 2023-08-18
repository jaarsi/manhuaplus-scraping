import logging
import logging.config
from typing import Literal

import requests

from .settings import DISCORD_WH

DefaultLoggers = Literal["series-scraping"]

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "series_scraping.logging.CustomFormatter",
            "format": "[ %(asctime)s ] [ %(author)s ] [ %(levelname)s ]\n%(message)s",
        },
        "discord": {
            "()": "series_scraping.logging.CustomFormatter",
            "format": ">>> **[ %(author)s ] [ %(levelname)s ]**\n%(message)s",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
        "discord": {
            "class": "series_scraping.logging.DiscordLoggingHandler",
            "formatter": "discord",
            "level": "INFO",
        },
    },
    "loggers": {
        "series-scraping": {"level": "DEBUG", "handlers": ["default", "discord"]}
    },
}


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


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: DefaultLoggers | None = None):
    return logging.getLogger(name)
