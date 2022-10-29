import logging

LOGGER_FORMAT = "%(asctime)s - [%(levelname)s]::[%(name)s -> %(funcName)s] || %(message)s"

def get_custom_logger(name: str, lvl: int = logging.INFO, format: str = LOGGER_FORMAT) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(lvl)
    logging.basicConfig(format=format, level=lvl)
    return logger

class ExceedTranslationLimit(Exception):
    pass

def translate_seconds_to_timer(n: int):
    if n >= 60 * 60:
        raise ExceedTranslationLimit(f"{n} is greater than an hour")
    minute = n // 60
    seconds = n % 60
    return f"{minute}:{seconds}"