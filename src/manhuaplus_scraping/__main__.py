import asyncio
import logging
import logging.config
import signal

import tomli
from redis import Redis

from .discord_bot import make_discord_bot
from .scraper import make_worker
from .settings import DISCORD_TOKEN, REDIS_HOST, REDIS_PORT


async def main():
    with open("settings.toml", mode="rb") as file:
        settings = tomli.load(file)

    logging.config.dictConfig(settings.get("logging"))  # type: ignore
    logger = logging.getLogger("manhuaplus_scraping")
    logger.info("Starting Manhuaplus scraping service.")
    series = settings.get("series", [])

    try:
        redis: Redis = Redis(REDIS_HOST, REDIS_PORT, 0, decode_responses=True)
        scraping_tasks = [make_worker(serie, redis) for serie in series]
        discord_bot_task = make_discord_bot(DISCORD_TOKEN, series)
        tasks = asyncio.gather(*[discord_bot_task, *scraping_tasks])

        def _handle_shutdown(*args):
            logger.warning("Shutdown order received ...")
            tasks.cancel()

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, _handle_shutdown)
        await tasks
    except Exception as error:
        logger.error("Unexpected error ocurred => %s", repr(error))

    logger.info("Manhuaplus scraping service is down.")


if __name__ == "__main__":
    asyncio.run(main())
