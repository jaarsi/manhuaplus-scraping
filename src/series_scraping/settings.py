import os
from pathlib import Path

DISCORD_WH = os.getenv("DISCORD_WH", None)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DATABASE_FILE = os.getenv("DATABASE_FILE", "docker/database.json")
