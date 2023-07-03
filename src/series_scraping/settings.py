import os
from pathlib import Path

DISCORD_WH = os.getenv("DISCORD_WH", None)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DEFAULT_APP_DIR = Path.home() / ".series-scraping"
APP_DIR = os.getenv("SERIES_SCRAPING_DATA_DIR", DEFAULT_APP_DIR)
DATABASE_FILE = os.path.join(APP_DIR, "database.json")
