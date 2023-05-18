import os

DISCORD_WH = os.getenv("DISCORD_WH", None)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DEFAULT_APP_DIR = os.path.join(os.getenv("HOME"), ".series-scraping")
APP_DIR = os.getenv("SERIES_SCRAPING_DATA_DIR", DEFAULT_APP_DIR)
DATABASE_FILE = os.path.join(APP_DIR, "database.json")
