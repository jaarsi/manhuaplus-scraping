import logging
import os

import requests

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


def get_logger(name: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    _stream_handler = logging.StreamHandler()
    _stream_handler.setFormatter(
        logging.Formatter(
            "[ %(asctime)s ] [ %(levelname)s ] [ %(author)s ] %(message)s",
            defaults={"author": "System"},
        )
    )
    logger.addHandler(_stream_handler)
    _discord_handler = DiscordLoggingHandler()
    _discord_handler.setFormatter(
        logging.Formatter(
            ">>> **[ %(asctime)s ]\n[ %(levelname)s ]\n[ %(author)s ]**\n%(message)s",
            defaults={"author": "System"},
        )
    )
    logger.addHandler(_discord_handler)
    return logger
