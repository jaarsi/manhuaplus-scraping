import os

import tomli

BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.toml")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DISCORD_WH = os.getenv("DISCORD_WH", None)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

with open(SETTINGS_FILE, mode="rb") as _file:
    _settings = tomli.load(_file)


LOGGING_CONFIG: dict = _settings["logging"]
SERIES: list[dict] = _settings["manhua"].get("series", [])
