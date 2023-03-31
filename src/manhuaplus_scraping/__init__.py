import logging
import os
import random
from datetime import datetime, timedelta
from typing import TypedDict

import gevent
import requests
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
        logger.error(repr(job.exception), extra={"author": serie["title"]})

    def _success_notifier(job):
        try:
            last_chapter: SerieChapterData = job.value
            serie_data: SerieChapterData = load_serie_data(serie, redis) or {
                **last_chapter,
                "chapter_number": 0,
                "chapter_url": "",
            }

            if last_chapter["chapter_number"] <= int(serie_data["chapter_number"]):
                # logger.info("No New Chapter Available ", extra={"author": serie["title"]})
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
            task.link_value(_success_notifier)
            task.link_exception(_error_notifier)
            task.start()
            task.join()
            now = datetime.now()
            next_checking_at = (now + timedelta(minutes=serie["check_interval"])).replace(
                second=0, microsecond=0
            )
            # logger.info(
            #     f"Next checking at {next_checking_at.isoformat()}.",
            #     extra={"author": serie["title"]},
            # )
            wait_time_seconds = (next_checking_at - now).seconds
            gevent.sleep(wait_time_seconds)

    return gevent.spawn(_loop)
