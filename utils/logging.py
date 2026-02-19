from loguru import logger
import sys

def set_initial_logging_config():
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

    logger.add(
        "dashboard.log",
        rotation="10 MB",
        retention="7 days",
    )
