import asyncio
import logging
from datetime import datetime, timedelta
from typing import TypedDict

import requests
from bs4 import BeautifulSoup
from redis import Redis

from . import settings


class Serie(TypedDict):
    title: str
    url: str
    store_key: str
    check_interval: list[int]


class SerieChapterData(TypedDict):
    chapter_number: int
    chapter_description: str
    chapter_url: str


def load_serie_data(serie: Serie, redis: Redis) -> SerieChapterData:
    return redis.hgetall(f"{serie['store_key']}-last-chapter")  # type: ignore


def save_serie_data(serie: Serie, data: SerieChapterData, redis: Redis) -> None:
    redis.hset(f"{serie['store_key']}-last-chapter", mapping=data)  # type: ignore


def fetch_last_chapter(serie: Serie) -> SerieChapterData:
    page_content = requests.get(
        serie["url"], headers={"User-Agent": settings.USER_AGENT}
    ).text
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


def next_checking_seconds(now: datetime, serie: Serie) -> int:
    try:
        next_interval_hour = [x for x in serie["check_interval"] if x > now.hour][0]
    except IndexError:
        next_interval_hour = serie["check_interval"][0]

    if next_interval_hour > now.hour:
        hours_interval = next_interval_hour - now.hour
    else:
        hours_interval = 24 - (now.hour - next_interval_hour)

    next_interval = (now + timedelta(hours=hours_interval)).replace(
        minute=0, second=0, microsecond=0
    )
    return int((next_interval - now).total_seconds())


def make_serie_scraper_worker(serie: Serie, redis: Redis):
    logger = logging.getLogger("manhuaplus_scraping")

    async def _error_notifier(error: Exception):
        logger.error(repr(error), extra={"author": serie["title"]})

    async def _success_notifier(last_chapter: SerieChapterData):
        try:
            serie_data: SerieChapterData = load_serie_data(serie, redis) or {
                **last_chapter,
                "chapter_number": 0,
                "chapter_url": "",
            }

            if last_chapter["chapter_number"] <= int(serie_data["chapter_number"]):
                return

            logger.info(
                "**New Chapter Available "
                f"[{serie_data['chapter_number']} => {last_chapter['chapter_number']}]**\n"
                f"{last_chapter['chapter_description']} \n"
                f"{last_chapter['chapter_url']}",
                extra={"author": serie["title"]},
            )
            save_serie_data(serie, last_chapter, redis)
        except Exception as error:
            logger.error(repr(error), extra={"author": serie["title"]})

    async def _worker():
        wait_time_seconds = next_checking_seconds(datetime.now(), serie)
        await asyncio.sleep(wait_time_seconds)

        try:
            result = await asyncio.to_thread(fetch_last_chapter, serie)
        except Exception as error:
            await _error_notifier(error)
        else:
            await _success_notifier(result)

    async def _loop():
        while True:
            await _worker()

    return _loop()
