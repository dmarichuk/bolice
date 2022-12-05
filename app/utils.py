import logging
import math

from config import BUILD_TYPE

LOGGER_FORMAT = (
    "%(asctime)s - [%(levelname)s]::[%(name)s -> %(funcName)s] || %(message)s"
)


def get_custom_logger(
    name: str, lvl: int = logging.INFO, format: str = LOGGER_FORMAT
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(lvl)
    if BUILD_TYPE == "PROD":
        logging.basicConfig(filename="/logs/bot.log", format=format, level=lvl)
    else:
        logging.basicConfig(format=format, level=lvl)
    return logger


class ExceedTranslationLimit(Exception):
    pass


def translate_seconds_to_timer(n: int | float) -> str:
    if n >= 60 * 60:
        raise ExceedTranslationLimit(f"{n} is greater than an hour")
    minute = int(n // 60)
    seconds = int(n % 60)
    return "{}:{}".format(str(minute).zfill(2), str(seconds).zfill(2))
