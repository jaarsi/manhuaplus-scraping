import asyncio
import traceback
from typing import Protocol
import requests
from datetime import datetime, timedelta

from . import types, logging, database
from bs4 import BeautifulSoup


logger = logging.get_logger("series-scraping")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)


class SerieScanScrapingStrategy(Protocol):
    def fetch_last_chapter(self, serie: types.Serie) -> types.SerieChapter:
        pass


class SingleSelectorStrategy(SerieScanScrapingStrategy):
    selector: str = None

    def fetch_last_chapter(self, serie: types.Serie) -> types.SerieChapter:
        response = requests.get(serie["url"], headers={"User-Agent": USER_AGENT})

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch site content [status_code={response.status_code}]"
            )

        page_content = response.text
        soup = BeautifulSoup(page_content, "lxml")
        chapter_element = soup.select(self.selector)[0]
        chapter_description = chapter_element.text.strip()
        _, chapter_number, *_ = chapter_description.split()
        chapter_link = chapter_element.attrs["href"]
        return {
            "chapter_description": chapter_description,
            "chapter_number": int(chapter_number),
            "chapter_url": chapter_link,
        }


class ManhuaPlusStrategy(SingleSelectorStrategy):
    selector = ".wp-manga-chapter:nth-child(1) a"


class AsuraScansStrategy(SingleSelectorStrategy):
    selector = "#chapterlist > ul > li:nth-child(1) > div > div > a"


strategies_mapping: dict[types.SerieScan, SerieScanScrapingStrategy] = {
    "manhuaplus": ManhuaPlusStrategy(),
    "asurascans": AsuraScansStrategy(),
}


def next_checking_seconds(serie: types.Serie, reference: datetime = None) -> int:
    reference = reference or datetime.now()

    try:
        next_interval_hour = [x for x in serie["check_interval"] if x > reference.hour][
            0
        ]
    except IndexError:
        next_interval_hour = serie["check_interval"][0]

    if next_interval_hour > reference.hour:
        hours_interval = next_interval_hour - reference.hour
    else:
        hours_interval = 24 - (reference.hour - next_interval_hour)

    next_interval = (reference + timedelta(hours=hours_interval)).replace(
        minute=0, second=0, microsecond=0
    )
    return int((next_interval - reference).total_seconds())


async def fetch_last_chapter(serie: types.Serie):
    scraper = strategies_mapping[serie["scan"]]
    result = await asyncio.to_thread(scraper.fetch_last_chapter, serie)
    return result


def listen_for_updates(serie: types.Serie):
    def _process_new_chapter(last_chapter: types.SerieChapter):
        serie_data = database.load_last_chapter(serie) or {
            **last_chapter,
            "chapter_number": 0,
            "chapter_url": "",
        }

        if last_chapter["chapter_number"] <= int(serie_data["chapter_number"]):
            return

        logger.info(
            "**New Chapter Available "
            f"[{serie_data['chapter_number']} => "
            f"{last_chapter['chapter_number']}]**\n"
            f"{last_chapter['chapter_description']} \n"
            f"{last_chapter['chapter_url']}",
            extra={"author": serie["title"]},
        )
        database.save_last_chapter(serie, last_chapter)

    async def _loop():
        while True:
            wait_time_seconds = next_checking_seconds(serie)
            await asyncio.sleep(wait_time_seconds)

            try:
                result = await fetch_last_chapter(serie)
                _process_new_chapter(serie, result)
            except Exception as error:
                logger.error(repr(error), extra={"author": serie["title"]})
                logger.debug(traceback.format_exc())

    return _loop()
