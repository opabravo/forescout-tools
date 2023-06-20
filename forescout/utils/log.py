"""
Loguru log configuration
"""
import sys
import logging
from loguru import logger
from loguru._defaults import LOGURU_FORMAT


def get_logger():
    logger.remove()
    logger.add(
        sys.stdout, 
        format="<level>{message}</level>",
        level=logging.getLevelName("INFO")
    )
    logger.add(
        "forescout.log", 
        format=LOGURU_FORMAT,
        level=logging.getLevelName("DEBUG"),
    )
    return logger

