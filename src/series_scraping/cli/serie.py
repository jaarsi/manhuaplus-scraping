import typer

from .. import database, types

app = typer.Typer()


@app.command()
def add(id: str, title: str, url: str, scan: types.SerieScan, check_interval: str):
    database.insert_serie(
        {
            "id": id,
            "title": title,
            "url": url,
            "scan": scan,
            "check_interval": list(map(int, check_interval.split(","))),
        }
    )
