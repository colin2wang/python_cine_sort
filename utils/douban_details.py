from typing import Optional

import requests

from utils import get_default_logger
from utils.common_util import sleep_for_random_time, bypass_douban_verification

# Get default logger
logger = get_default_logger()


def get_movie_details_html(sid: str) -> Optional[str]:
    """Get Douban movie details page HTML content (automatically handles verification mechanism)

    Args:
        sid (str): Movie SID

    Returns:
        Optional[str]: HTML response content, returns None on failure
    """
    # Build search URL
    url = f'https://movie.douban.com/subject/{sid}/'
    
    try:
        # Use function with verification handling to get page content
        logger.info(f"Getting movie details for SID: {sid}")
        sleep_for_random_time()
        response = bypass_douban_verification(url)
        
        # Set correct encoding
        response.encoding = 'utf-8'
        
        logger.info(f"✓ Successfully retrieved Douban movie details: {sid}")
        return response.text
        
    except requests.exceptions.Timeout:
        logger.warning(f"✗ Request timeout: {sid}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Connection error: {sid}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"✗ HTTP error {e.response.status_code}: {sid}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Request exception: {e} - {sid}")
        return None
    except Exception as e:
        logger.error(f"✗ Unknown error: {e} - {sid}")
        return None

def parse_movie_details_result(html_content: str) -> dict:
    """Parse Douban movie details page
    
    Args:
        html_content (str): Douban movie details page HTML content
    
    Returns:
        dict: Parsed movie information
    """
    import re
    
    # Parameter validation
    if html_content is None:
        logger.error("✗ HTML content is None")
        return {}
    
    if not isinstance(html_content, str):
        logger.error(f"✗ HTML content type error: {type(html_content)}")
        return {}
    
    try:
        movie_details = {}
        
        # Extract movie title
        title_pattern = r'<span property="v:itemreviewed">([^<]+)</span>'
        title_match = re.search(title_pattern, html_content)
        if title_match:
            movie_details['title'] = title_match.group(1).strip()
        
        # Extract rating
        rating_pattern = r'<strong class="ll rating_num" property="v:average">([\d.]+)</strong>'
        rating_match = re.search(rating_pattern, html_content)
        if rating_match:
            movie_details['rating'] = rating_match.group(1)
        
        # Extract year
        year_pattern = r'<span class="year">\((\d{4})\)</span>'
        year_match = re.search(year_pattern, html_content)
        if year_match:
            movie_details['year'] = year_match.group(1)
        
        # Extract directors
        director_pattern = r'导演:</span>.*?<a[^>]*>([^<]+)</a>'
        director_matches = re.findall(director_pattern, html_content, re.DOTALL)
        if director_matches:
            movie_details['directors'] = [director.strip() for director in director_matches]
        
        # Extract actors
        actor_pattern = r'主演:</span>.*?<a[^>]*>([^<]+)</a>'
        actor_matches = re.findall(actor_pattern, html_content, re.DOTALL)
        if actor_matches:
            movie_details['actors'] = [actor.strip() for actor in actor_matches[:5]]  # Take first 5
        
        # Extract genres
        genre_pattern = r'<span property="v:genre">([^<]+)</span>'
        genre_matches = re.findall(genre_pattern, html_content)
        if genre_matches:
            movie_details['genres'] = [genre.strip() for genre in genre_matches]
        
        # Extract description
        description_pattern = r'<span property="v:summary" class="all hidden">([^<]+)</span>'
        description_match = re.search(description_pattern, html_content, re.DOTALL)
        if description_match:
            movie_details['description'] = description_match.group(1).strip()
        else:
            # Try alternative description format
            alt_desc_pattern = r'<span property="v:summary">([^<]+)</span>'
            alt_desc_match = re.search(alt_desc_pattern, html_content, re.DOTALL)
            if alt_desc_match:
                movie_details['description'] = alt_desc_match.group(1).strip()
        
        # Extract original title
        original_title_pattern = r'又名:</span>([^<]+)'
        original_title_match = re.search(original_title_pattern, html_content)
        if original_title_match:
            movie_details['original_title'] = original_title_match.group(1).strip()
        
        logger.info(f"✓ Successfully parsed movie details: {movie_details.get('title', 'Unknown')}")
        return movie_details
        
    except Exception as e:
        logger.error(f"✗ Error parsing movie details: {e}")
        return {}