#!.venv/bin/python
import os
import asyncio
import requests
import logging
from redis import Redis
from playwright.async_api import async_playwright, Page, Frame
from dotenv import load_dotenv

load_dotenv()
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 120))
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
redis = Redis("localhost", REDIS_PORT, 0)
redis.ping()

async def comment_and_post(page: Page, message: str):
    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    p: Frame = page.main_frame.child_frames[2]
    element = await p.wait_for_selector(
        "#form > form > div > div.compose-wrapper > div.textarea-outer-wrapper > div > div:nth-child(1) > div.textarea > p"
    )
    element.text_content = message
    element = await p.wait_for_selector(
        "#form > form > div > div.compose-wrapper > div.textarea-outer-wrapper"\
        " > div > div.text-editor-container > div > div.logged-in > section > "\
        "div > button.btn.post-action__button.full-size-button"
    )
    await element.click()


def send_discord_message(message: str):
    webhook_url = "https://discord.com/api/webhooks/1046665729166020648/"\
        "BhO1w3r65bDEol449m9H39qrEbfOacFSq6jCR4RawMUviIozGqq3CNNDn5c5g3PvBDGV"

    try:
        requests.post(webhook_url, json={ "content": message, "flags": 4 })
    except:
        pass

async def worker():
    async with async_playwright() as p:
        browser = await p.firefox.launch()

        try:
            page = await browser.new_page()
            await page.goto("https://manhuaplus.com/manga/martial-peak/", wait_until="domcontentloaded")
            element = await page.locator(".wp-manga-chapter:nth-child(1) a").element_handle()
            _, value, *_ = (await element.text_content()).split()
            last_chapter_available = int(value)
            last_chapter_available_link = await element.get_attribute("href")
            last_chapter_saved = int(redis.get("last_chapter") or last_chapter_available)
            redis.set("last_chapter", last_chapter_available)

            if last_chapter_available <= last_chapter_saved:
                logging.info("No New Chapter Available")
                return

            logging.warning("New Chapter Available")
            send_discord_message(
                f"New Chapter Available: {last_chapter_saved} => {last_chapter_available}\n"
                f"{last_chapter_available_link}"
            )
            await page.goto(last_chapter_available_link, wait_until="load")
            # await comment_and_post(page, "First")
        finally:
            await browser.close()

async def loop():
    while True:
        try:
            logging.info("Running Worker ...")
            await worker()
        except Exception as error:
            logging.error("An error ocurred: %s", str(error))
        finally:
            await asyncio.sleep(120)

try:
    asyncio.run(loop())
except Exception as error:
    print(str(error))