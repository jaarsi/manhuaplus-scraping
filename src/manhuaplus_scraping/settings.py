import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DISCORD_WH = os.getenv("DISCORD_WH", None)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
