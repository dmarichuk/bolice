import logging

LOGGER_FORMAT = "%(asctime)s - [%(levelname)s]::[%(name)s -> %(funcName)s] || %(message)s"

def get_custom_logger(name: str, lvl: int = logging.INFO, format: str = LOGGER_FORMAT) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(lvl)
    logging.basicConfig(format=format)
    return logger
