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
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 120))
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
        f"[ {task_result.serie.title}] "
        "New Chapter Available: {task_result.last_chapter_saved} => {task_result.new_chapter_available}\n"
        f"{task_result.new_chapter_url}"
    )

    try:
        requests.post(
            task_result.serie.discord_wh, json={"content": message, "flags": 4}
        )
    except:
        pass


async def worker(browser: Browser, serie: Serie) -> ScrapingTaskResult:
    page = await browser.new_page()
    await page.goto(serie.url, wait_until="domcontentloaded")
    element = page.locator(".wp-manga-chapter:nth-child(1) a")
    _, value, *_ = (await element.text_content()).split()
    last_chapter_available = int(value)
    last_chapter_available_link = await element.get_attribute("href")
    last_chapter_saved = int(
        redis.hget(serie.store_key, "last-chapter") or last_chapter_available
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


async def _main():
    with open("series.toml", mode="r") as file:
        content = toml.load(file)

    series = [Serie(**item) for item in content["series"]]

    while True:
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            tasks = [worker(browser, serie) for serie in series]

            try:
                results: list[ScrapingTaskResult] = await asyncio.gather(*tasks)

                for result in results:
                    if not result.new_chapter_available:
                        logger.info(f"{result.serie.title}: No New Chapter Available.")
                        continue

                    send_discord_new_chapter_notification(result)

            except Exception as error:
                logger.error("An error ocurred: %s", str(error))
            finally:
                await browser.close()
                await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
