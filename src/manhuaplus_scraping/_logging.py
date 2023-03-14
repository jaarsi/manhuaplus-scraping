import logging
import logging.config
import os

import requests
import toml

DISCORD_WH = os.getenv("DISCORD_WH", None)


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


def get_logger(name: str) -> logging.Logger:
    path = os.path.join(os.path.dirname(__file__), "_logging.toml")

    with open(path) as file:
        config = toml.load(file)

    logging.config.dictConfig(config)
    return logging.getLogger(name)
