import os

from . import cli, logging, settings

logging.setup_logging()
logger = logging.get_logger("series-scraping")


if __name__ == "__main__":
    cli.app()
