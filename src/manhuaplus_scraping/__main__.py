import asyncio
import logging
import os
import signal
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests
import toml
from playwright.async_api import (
    Browser,
    BrowserContext,
    TimeoutError,
    async_playwright,
)
from redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DISCORD_WH = os.getenv("DISCORD_WH", None)


class DiscordLoggingHandler(logging.Handler):
    def _send_discord_notification(self, message: str):
        if not (DISCORD_WH and message):
            return

        try:
            requests.post(DISCORD_WH, json={"content": message, "flags": 4})
        except Exception:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        if not record.msg:
            return

        message = f"```{self.format(record)}```"
        self._send_discord_notification(message)


logging.basicConfig(
    level=logging.INFO,
    format="[ %(asctime)s ] [ %(levelname)s ] %(message)s",
    handlers=[logging.StreamHandler(), DiscordLoggingHandler()],
)
redis: Redis = Redis(REDIS_HOST, REDIS_PORT, 0)


@dataclass
class Serie:
    title: str
    url: str
    store_key: str
    check_intervals: list[int]


@dataclass
class ScrapingTaskResult:
    serie: Serie
    last_chapter_saved: int
    is_new_chapter_available: bool
    new_chapter_number: int | None = field(default=None)
    new_chapter_url: str | None = field(default=None)


async def check_new_chapter_task(
    context: BrowserContext, serie: Serie
) -> ScrapingTaskResult:
    try:
        page = await context.new_page()
        page.set_default_timeout(5000)
        await page.goto(serie.url, wait_until="domcontentloaded")
        element = page.locator(".wp-manga-chapter:nth-child(1) a")
        _, value, *_ = (await element.text_content()).split()
        last_chapter_available = int(value)
        last_chapter_available_link = await element.get_attribute("href")
        last_chapter_saved = int(
            redis.hget(serie.store_key, "last-chapter")
            or last_chapter_available
        )
        redis.hset(serie.store_key, "last-chapter", last_chapter_available)

        if last_chapter_available <= last_chapter_saved:
            return ScrapingTaskResult(serie, last_chapter_saved, False)

        return ScrapingTaskResult(
            serie,
            last_chapter_saved,
            True,
            last_chapter_available,
            last_chapter_available_link,
        )
    finally:
        await context.close()


def get_next_checking(serie: Serie) -> datetime:
    now = datetime.now()

    try:
        next_interval_hour = [
            x for x in serie.check_intervals if x > now.hour
        ][0]
    except IndexError:
        next_interval_hour = serie.check_intervals[0]

    if next_interval_hour > now.hour:
        hours_interval = next_interval_hour - now.hour
    else:
        hours_interval = 24 - (now.hour - next_interval_hour)

    next_interval = (now + timedelta(hours=hours_interval)).replace(
        minute=0, second=0, microsecond=0
    )
    return next_interval


async def worker(browser: Browser, serie: Serie):
    async def _worker():
        next_checking_at = get_next_checking(serie)
        logging.info(
            f"[ {serie.title} ] Next checking at {next_checking_at.isoformat()}."
        )
        wait_seconds_interval = (next_checking_at - datetime.now()).seconds
        await asyncio.sleep(wait_seconds_interval)

        try:
            result = await check_new_chapter_task(
                await browser.new_context(), serie
            )
        except TimeoutError as error:
            logging.warning(f"[ {serie.title} ] {error.message}")
        else:
            if not result.is_new_chapter_available:
                logging.info(f"[ {serie.title} ] No New Chapter Available.")
                return

            logging.info(
                f"[ {result.serie.title} ] "
                f"New Chapter Available {result.last_chapter_saved} => "
                f"{result.new_chapter_number}\n"
                f"{result.new_chapter_url}"
            )

    while True:
        await _worker()


async def _main():
    redis.ping()

    with open("manhuaplus-series.toml", mode="r") as file:
        content = toml.load(file)

    series = [Serie(**item) for item in content["series"]]

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        job = asyncio.gather(*[worker(browser, serie) for serie in series])
        asyncio.get_event_loop().add_signal_handler(
            signal.SIGTERM, lambda *args: job.cancel()
        )

        try:
            await job
        except asyncio.CancelledError:
            logging.warning("Cancel scraping order received.")
        except Exception as error:
            job.cancel(str(error))
        finally:
            await browser.close()


def main():
    logging.info("Starting Manhuaplus scraping service.")

    try:
        asyncio.run(_main())
    except Exception as error:
        logging.error("Unexpected error ocurred => %s", str(error))

    logging.info("Manhuaplus scraping service is down.")


if __name__ == "__main__":
    main()
