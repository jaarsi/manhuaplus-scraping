import asyncio
import logging
import os
from dataclasses import dataclass, field

import requests
import toml
from playwright.async_api import Browser, async_playwright
from redis import Redis

WEBHOOK_URL = (
    "https://discord.com/api/webhooks/1046665729166020648/"
    "BhO1w3r65bDEol449m9H39qrEbfOacFSq6jCR4RawMUviIozGqq3CNNDn5c5g3PvBDGV"
)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
logger = logging.getLogger("manhuaplus-scraping")
logger.addHandler(sh := logging.StreamHandler())
sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.setLevel(logging.INFO)
redis: Redis = Redis(REDIS_HOST, REDIS_PORT, 0)


@dataclass
class Serie:
    title: str
    url: str
    store_key: str
    discord_wh: str
    check_interval: int


@dataclass
class ScrapingTaskResult:
    serie: Serie
    last_chapter_saved: int
    new_chapter_available: bool
    new_chapter: int | None = field(default=None)
    new_chapter_url: str | None = field(default=None)


def main():
    try:
        redis.ping()
        asyncio.run(_main())
    except Exception as error:
        logger.error(str(error))


def send_discord_new_chapter_notification(task_result: ScrapingTaskResult):
    message = (
        f"[ {task_result.serie.title} ] "
        f"New Chapter Available {task_result.last_chapter_saved} => "
        f"{task_result.new_chapter_available}\n"
        f"{task_result.new_chapter_url}"
    )

    try:
        requests.post(
            task_result.serie.discord_wh, json={"content": message, "flags": 4}
        )
    except Exception:
        pass


async def check_new_chapter_task(
    browser: Browser, serie: Serie
) -> ScrapingTaskResult:
    try:
        page = await browser.new_page()
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
        await page.close()


async def _main():
    with open("manhuaplus-series.toml", mode="r") as file:
        content = toml.load(file)

    series = [Serie(**item) for item in content["series"]]

    async with async_playwright() as p:
        browser = await p.firefox.launch()

        async def worker(serie: Serie):
            while True:
                try:
                    result = await check_new_chapter_task(browser, serie)

                    if not result.new_chapter_available:
                        logger.info(
                            f"[ {serie.title} ] No New Chapter Available."
                        )
                        continue

                    send_discord_new_chapter_notification(result)
                finally:
                    await asyncio.sleep(serie.check_interval)

        job = asyncio.gather(*[worker(serie) for serie in series])

        try:
            await job
        except Exception as error:
            logger.error("An error ocurred: %s", str(error))
            job.cancel(str(error))
        finally:
            await browser.close()


if __name__ == "__main__":
    main()
