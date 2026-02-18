import random
import time

from .logging_util import get_default_logger

logger = get_default_logger()


def sleep_for_random_time():
    sleep_time = random.uniform(0.5, 1.5)
    logger.info(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)
