import asyncio
import logging
import os

import requests
from playwright.async_api import async_playwright
from redis import Redis

WEBHOOK_URL = (
    "https://discord.com/api/webhooks/1046665729166020648/"
    "BhO1w3r65bDEol449m9H39qrEbfOacFSq6jCR4RawMUviIozGqq3CNNDn5c5g3PvBDGV"
)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 120))
logger = logging.getLogger("manhuaplus-scraping")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
redis = Redis(REDIS_HOST, REDIS_PORT, 0)


def main():
    try:
        redis.ping()
        asyncio.run(_main())
    except Exception as error:
        logger.error(str(error))


def send_discord_message(message: str):
    try:
        requests.post(WEBHOOK_URL, json={"content": message, "flags": 4})
    except:
        pass


async def worker():
    async with async_playwright() as p:
        browser = await p.firefox.launch()

        try:
            page = await browser.new_page()
            await page.goto(
                "https://manhuaplus.com/manga/martial-peak/",
                wait_until="domcontentloaded",
            )
            element = await page.locator(
                ".wp-manga-chapter:nth-child(1) a"
            ).element_handle()
            _, value, *_ = (await element.text_content()).split()
            last_chapter_available = int(value)
            last_chapter_available_link = await element.get_attribute("href")
            last_chapter_saved = int(
                redis.get("last_chapter") or last_chapter_available
            )
            redis.set("last_chapter", last_chapter_available)

            if last_chapter_available <= last_chapter_saved:
                logger.info(f"No New Chapter Available")
                logger.info(f"{last_chapter_available=} {last_chapter_saved=}")
                return

            logger.warning("New Chapter Available")
            send_discord_message(
                f"New Chapter Available: {last_chapter_saved} => {last_chapter_available}\n"
                f"{last_chapter_available_link}"
            )
            await page.goto(last_chapter_available_link, wait_until="load")
        finally:
            await browser.close()


async def _main():
    while True:
        try:
            logger.info("Running Worker ...")
            await worker()
        except Exception as error:
            logger.error("An error ocurred: %s", str(error))
        finally:
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
