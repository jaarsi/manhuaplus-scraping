import asyncio
from datetime import datetime, timedelta

from .. import logging, database
from . import strategies, types


logger = logging.get_logger("series-scraping")
strategies_mapping: dict[types.SerieScan, strategies.SerieScanScrapingStrategy] = {
    "manhuaplus": strategies.ManhuaPlusStrategy(),
    "asurascans": strategies.AsuraScansStrategy(),
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


def _process_new_chapter(serie: types.Serie, last_chapter: types.SerieChapter):
    try:
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
    except Exception as error:
        logger.error(repr(error), extra={"author": serie["title"]})


async def fetch_last_chapter(serie: types.Serie):
    scraper = strategies_mapping[serie["scan"]]
    return await asyncio.to_thread(scraper.fetch_last_chapter, serie)


def listen_for_updates(serie: types.Serie):
    async def _loop():
        while True:
            wait_time_seconds = next_checking_seconds(serie)
            await asyncio.sleep(wait_time_seconds)

            try:
                result = await fetch_last_chapter(serie)
            except Exception as error:
                logger.error(repr(error), extra={"author": serie["title"]})
            else:
                _process_new_chapter(serie, result)

    return _loop()
