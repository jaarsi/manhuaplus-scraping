import logging
import logging.config
import signal

import gevent
import tomli
from redis import Redis

from . import REDIS_HOST, REDIS_PORT, make_worker


def main():
    with open("settings.toml", mode="rb") as file:
        settings = tomli.load(file)

    logging.config.dictConfig(settings.get("logging"))  # type: ignore
    logger = logging.getLogger("manhuaplus_scraping")
    logger.info("Starting Manhuaplus scraping service.")
    series = settings.get("series", [])

    try:
        redis: Redis = Redis(REDIS_HOST, REDIS_PORT, 0, decode_responses=True)
        tasks = [make_worker(serie, redis) for serie in series]

        def _handle_shutdown(*args):
            logger.warning("Shutdown order received ...")
            gevent.killall(tasks, block=False)

        signal.signal(signal.SIGTERM, _handle_shutdown)
        signal.signal(signal.SIGINT, _handle_shutdown)
        gevent.joinall(tasks, raise_error=True)
    except Exception as error:
        logger.error("Unexpected error ocurred => %s", repr(error))

    logger.info("Manhuaplus scraping service is down.")


if __name__ == "__main__":
    main()
