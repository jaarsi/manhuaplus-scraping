import asyncio
import logging
import logging.config
import signal

import tomli
from redis import Redis

from .discord_bot import make_discord_bot
from .scraper import make_serie_scraper_worker
from .settings import DISCORD_TOKEN, REDIS_HOST, REDIS_PORT


def main():
    with open("settings.toml", mode="rb") as file:
        settings = tomli.load(file)

    logging.config.dictConfig(settings.get("logging"))  # type: ignore
    logger = logging.getLogger("manhuaplus_scraping")
    logger.info("Starting Manhuaplus scraping service.")
    redis: Redis = Redis(REDIS_HOST, REDIS_PORT, 0, decode_responses=True)
    series = settings.get("series", [])

    async def _main():
        series_scraping_workers = [
            make_serie_scraper_worker(serie, redis) for serie in series
        ]
        discord_bot_worker = make_discord_bot(DISCORD_TOKEN, series)
        tasks = asyncio.gather(*[discord_bot_worker, *series_scraping_workers])

        def _handle_shutdown(*args):
            logger.warning("Shutdown order received ...")
            tasks.cancel()

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, _handle_shutdown)
        loop.add_signal_handler(signal.SIGINT, _handle_shutdown)
        await tasks

    try:
        asyncio.run(_main())
    except Exception as error:
        logger.error("Unexpected error ocurred => %s", repr(error))
    except BaseException:
        pass
    finally:
        logger.info("Manhuaplus scraping service is down.")


if __name__ == "__main__":
    main()
