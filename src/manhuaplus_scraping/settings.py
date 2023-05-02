import os
import tomli

BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings", "settings.toml")
LOGGING_FILE = os.path.join(BASE_DIR, "settings", "logging.toml")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DISCORD_WH = os.getenv("DISCORD_WH", None)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

with open(LOGGING_FILE, mode="rb") as _file:
    LOGGING_CONFIG: dict = tomli.load(_file)

with open(SETTINGS_FILE, mode="rb") as _file:
    SERIES: list = tomli.load(_file).get("series", [])
