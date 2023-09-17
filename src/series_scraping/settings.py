import os

from dotenv import load_dotenv

load_dotenv()
DISCORD_WH = os.getenv("DISCORD_WH", None)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DATABASE_FILE = os.getenv("DATABASE_FILE", "database.json")
