from typing import TypedDict, Literal


SerieScan = Literal["manhuaplus", "asurascans"]


class Serie(TypedDict):
    id: str
    title: str
    url: str
    scan: SerieScan
    check_interval: list[int]


class SerieChapter(TypedDict):
    chapter_number: int
    chapter_description: str
    chapter_url: str
