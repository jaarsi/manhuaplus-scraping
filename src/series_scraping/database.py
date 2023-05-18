from tinydb import TinyDB, where
from contextlib import contextmanager
from .settings import DATABASE_FILE
from .series import Serie, SerieChapter


@contextmanager
def get_session(table: str):
    with TinyDB(DATABASE_FILE, sort_keys=True, indent=4) as db:
        yield db.table(table)


def load_last_chapter(serie: Serie) -> SerieChapter:
    with get_session("last-chapters") as db:
        return db.get(where("id") == serie["id"])


def save_last_chapter(serie: Serie, chapter: SerieChapter) -> None:
    with get_session("last-chapters") as db:
        db.upsert({"id": serie["id"], **chapter}, where("id") == serie["id"])


def load_series() -> list[Serie]:
    with get_session("series") as db:
        return db.all()


def insert_serie(serie: Serie):
    with get_session("series") as db:
        db.upsert(serie, where("id") == serie["id"])
