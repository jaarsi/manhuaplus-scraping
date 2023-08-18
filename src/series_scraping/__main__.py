import os

from . import cli, logging, settings

logging.setup_logging()
logger = logging.get_logger("series-scraping")
os.makedirs(settings.APP_DIR, exist_ok=True)


if __name__ == "__main__":
    cli.app()