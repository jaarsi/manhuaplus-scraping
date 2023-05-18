import typer
from . import scrape
from . import serie

app = typer.Typer(name="series-scraping")
app.add_typer(scrape.app, name="scrape")
app.add_typer(serie.app, name="serie")
