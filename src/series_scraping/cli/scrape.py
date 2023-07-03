import asyncio
import signal

import typer

from .. import database, discord_bot, logging, scraper, settings

logger = logging.get_logger("series-scraping")
app = typer.Typer()


@app.command()
def start():
    logger.info("Starting Manhuaplus scraping service.")

    async def _main():
        _series = database.load_series()
        tasks = [discord_bot.start_discord_bot(settings.DISCORD_TOKEN, _series)]
        tasks.extend(map(scraper.listen_for_updates, _series))
        main_task = asyncio.gather(*tasks)

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
