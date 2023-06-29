from typing import Protocol
import requests
from bs4 import BeautifulSoup
from .types import Serie, SerieChapter


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)


class SerieScanScrapingStrategy(Protocol):
    def fetch_last_chapter(self, serie: Serie) -> SerieChapter:
        pass


class SingleSelectorStrategy(SerieScanScrapingStrategy):
    selector: str = ""

    def fetch_last_chapter(self, serie: Serie) -> SerieChapter:
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
