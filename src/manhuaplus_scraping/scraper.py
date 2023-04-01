import asyncio
import logging
from datetime import datetime, timedelta
from typing import TypedDict

import arrow
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
    page_content = requests.get(serie["url"], headers={"User-Agent": settings.USER_AGENT}).text
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


def calculate_next_checking(serie: Serie) -> datetime:
    now = datetime.now()

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
    return next_interval


async def make_worker(serie: Serie, redis: Redis) -> None:
    logger = logging.getLogger("manhuaplus_scraping")

    def _error_notifier(error: Exception):
        logger.error(repr(error), extra={"author": serie["title"]})

    def _success_notifier(last_chapter: SerieChapterData):
        try:
            serie_data: SerieChapterData = load_serie_data(serie, redis) or {
                **last_chapter,
                "chapter_number": 0,
                "chapter_url": "",
            }

            if last_chapter["chapter_number"] <= int(serie_data["chapter_number"]):
                # logger.info("No New Chapter Available", extra={"author": serie["title"]})
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

    async def _wait_for_checking_time():
        try:
            now = datetime.now()
            next_checking_at = calculate_next_checking(serie)
            human_time = arrow.get(next_checking_at + timedelta(minutes=1)).humanize(
                other=now, granularity=["hour", "minute"]
            )
            logger.info(f"Next checking {human_time}.", extra={"author": serie["title"]})
            wait_time_seconds = (next_checking_at - now).total_seconds()
            await asyncio.sleep(wait_time_seconds)
        except Exception as error:
            logger.error(repr(error), extra={"author": serie["title"]})

    async def _loop():
        while True:
            await _wait_for_checking_time()

            try:
                result = fetch_last_chapter(serie)
            except Exception as error:
                _error_notifier(error)
            else:
                _success_notifier(result)

    await _loop()
