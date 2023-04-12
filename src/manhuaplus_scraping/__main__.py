import asyncio
import logging
import logging.config
import signal

from . import discord_bot, manhua, settings
from .settings import LOGGING_CONFIG


def main():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("manhuaplus_scraping")
    logger.info("Starting Manhuaplus scraping service.")

    async def _main():
        _tasks = [
            manhua.listen_for_updates(serie) for serie in settings.SERIES  # type: ignore
        ]
        _tasks.append(
            discord_bot.start_discord_bot(settings.DISCORD_TOKEN, settings.SERIES)  # type: ignore
        )
        main_task = asyncio.gather(*_tasks)

        def _handle_shutdown(*args):
            logger.warning("Shutdown order received ...")
            main_task.cancel()

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, _handle_shutdown)
        loop.add_signal_handler(signal.SIGINT, _handle_shutdown)
        await main_task

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
