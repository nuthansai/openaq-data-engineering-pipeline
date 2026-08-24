import logging
from logging.handlers import TimedRotatingFileHandler

from src.config import LOG_DIR

formatter = logging.Formatter(
    "{asctime} - {name} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M"
)

handler = TimedRotatingFileHandler(
    filename=LOG_DIR/"app.log",
    when="D",
    interval=60,
    backupCount=30,
    utc=True
)

handler.suffix = "%Y-%m-%d"
handler.setFormatter(formatter)


handler.setLevel(logging.DEBUG)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)