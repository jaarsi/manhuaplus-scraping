import logging
import logging.config
import os
import signal
from datetime import datetime, timedelta
from typing import TypedDict

import gevent
import requests
import tomli
from bs4 import BeautifulSoup
from redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DISCORD_WH = os.getenv("DISCORD_WH", None)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)


class DiscordLoggingHandler(logging.Handler):
    def _send_discord_notification(self, message: str):
        if not (DISCORD_WH and message):
            return

        try:
            requests.post(DISCORD_WH, json={"content": message, "flags": 4})
        except:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        if not record.msg:
            return

        self._send_discord_notification(self.format(record))


class CustomFormatter(logging.Formatter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, defaults={"author": "System"})


class Serie(TypedDict):
    title: str
    url: str
    store_key: str
    check_interval: int


class SerieChapterData(TypedDict):
    chapter_number: int
    chapter_description: str
    chapter_url: str


def load_serie_data(serie: Serie, redis: Redis) -> SerieChapterData:
    return redis.hgetall(serie["store_key"])  # type: ignore


def save_serie_data(serie: Serie, data: SerieChapterData, redis: Redis) -> None:
    redis.hset(serie["store_key"], mapping=data)  # type: ignore


def check_new_chapter(serie: Serie) -> SerieChapterData:
    page_content = requests.get(serie["url"], headers={"User-Agent": USER_AGENT}).text
    soup = BeautifulSoup(page_content, "lxml")
    chapter_element = soup.select(".wp-manga-chapter:nth-child(1) a")[0]
    chapter_description = chapter_element.text.strip()
    _, chapter_number, *_ = chapter_description.split()
    chapter_link = chapter_element.attrs["href"]
    return {
        "chapter_description": chapter_description,
        "chapter_number": int(chapter_number),
        "chapter_url": chapter_link,
    }


def make_worker(serie: Serie, redis: Redis) -> gevent.Greenlet:
    logger = logging.getLogger("manhuaplus_scraping")

    def _error_notifier(job):
        logger.error(str(job.exception), extra={"author": serie["title"]})

    def _new_chapter_notifier(job):
        try:
            last_chapter: SerieChapterData = job.value
            serie_data: SerieChapterData = load_serie_data(serie, redis) or {
                **last_chapter,
                "chapter_number": 0,
                "chapter_url": "",
            }

            if last_chapter["chapter_number"] <= int(serie_data["chapter_number"]):
                logger.info("No New Chapter Available ", extra={"author": serie["title"]})
                return

            logger.info(
                "New Chapter Available "
                f"{serie_data['chapter_number']} => {last_chapter['chapter_number']}\n"
                f"{last_chapter['chapter_url']}",
                extra={"author": serie["title"]},
            )
            save_serie_data(serie, last_chapter, redis)
        except Exception as error:
            logger.error(repr(error), extra={"author": serie["title"]})

    def _loop():
        while True:
            task = gevent.Greenlet(check_new_chapter, serie)
            task.link_value(_new_chapter_notifier)
            task.link_exception(_error_notifier)
            task.start()
            task.join()
            now = datetime.now()
            next_checking_at = now + timedelta(seconds=serie["check_interval"])
            logger.info(
                f"Next checking at {next_checking_at.isoformat()}.",
                extra={"author": serie["title"]},
            )
            wait_time_seconds = (next_checking_at - now).seconds
            gevent.sleep(wait_time_seconds)

    return gevent.spawn(_loop)


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
        logger.error("Unexpected error ocurred => %s", str(error))

    logger.info("Manhuaplus scraping service is down.")
