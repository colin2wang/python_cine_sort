"""IMDB rating fetcher.

Fetches movie rating from IMDB using the public GraphQL API.
"""

import re
from typing import Optional

import requests

from utils.common_util import sleep_for_random_time
from utils.logging_config import setup_logger

logger = setup_logger(__name__)

_GRAPHQL_URL = 'https://graphql.imdb.com/'
_GRAPHQL_QUERY = """
query {
  title(id: "%s") {
    ratingsSummary {
      aggregateRating
      voteCount
    }
  }
}
"""


def get_imdb_rating(imdb_id: str) -> Optional[float]:
    """Fetch IMDB rating by title ID.

    Args:
        imdb_id: IMDB title ID (e.g. "tt1826590")

    Returns:
        Rating as float (e.g. 6.7), or None on failure
    """
    if not imdb_id or not imdb_id.startswith('tt'):
        logger.warning(f"Invalid IMDB ID: {imdb_id}")
        return None

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        logger.info(f"Fetching IMDB rating for: {imdb_id}")
        sleep_for_random_time()

        payload = {'query': _GRAPHQL_QUERY % imdb_id}
        response = requests.post(_GRAPHQL_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        rating = data.get('data', {}).get('title', {}).get('ratingsSummary', {}).get('aggregateRating')

        if rating is not None:
            result = float(rating)
            logger.info(f"✓ IMDB rating for {imdb_id}: {result}")
            return result

        logger.warning(f"No rating found for IMDB ID: {imdb_id}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch IMDB rating for {imdb_id}: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse IMDB response for {imdb_id}: {e}")
        return None
