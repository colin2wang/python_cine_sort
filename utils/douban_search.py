import requests
from typing import Optional

from utils import get_default_logger
from utils.common_util import sleep_for_random_time

# Get default logger
logger = get_default_logger()


def get_movie_search_result_html(name: str, year: str) -> Optional[str]:
    """Get Douban movie search results
    
    Args:
        name (str): Movie name
        year (str): Movie year
    
    Returns:
        Optional[str]: HTML response content, returns None on failure
    """
    # Build search URL
    url = f'https://www.douban.com/search?cat=1002&q={name} {year}'
    
    # Set request headers to simulate browser access
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Send GET request
        logger.info(f"GET {url}")
        sleep_for_random_time()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Check HTTP status code
        
        # Set correct encoding
        response.encoding = 'utf-8'
        
        logger.info(f"✓ Successfully retrieved Douban search results: {name} ({year})")
        return response.text
        
    except requests.exceptions.Timeout:
        logger.warning(f"✗ Request timeout: {name} ({year})")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Connection error: {name} ({year})")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"✗ HTTP error {e.response.status_code}: {name} ({year})")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Request exception: {e} - {name} ({year})")
        return None
    except Exception as e:
        logger.error(f"✗ Unknown error: {e} - {name} ({year})")
        return None


def _create_empty_movie_info(error_message: str = None) -> dict:
    """Create empty movie info dictionary
    
    Args:
        error_message (str, optional): Error message
        
    Returns:
        dict: Empty movie info dictionary
    """
    return {
        'title': '',
        'rating': '',
        'description': '',
        'directors': [],
        'actors': [],
        'year': '',
        'genres': [],
        'original_title': '',
        'review_count': '',
        'sid': '',
        'error': error_message
    }


def parse_movie_search_result(html_content: str) -> dict:
    """Parse movie information from Douban search results (using regex)
    
    Args:
        html_content (str): Douban search page HTML content
    
    Returns:
        dict: Parsed movie information
    """
    import re
    
    # Parameter validation
    if html_content is None:
        logger.error("✗ HTML content is None")
        return _create_empty_movie_info('Parsing error: HTML content is empty')
    
    if not isinstance(html_content, str):
        logger.error(f"✗ HTML content type error: {type(html_content)}")
        return _create_empty_movie_info(f'Parsing error: Expected string type, got {type(html_content).__name__}')
    
    try:
        movie_info = _create_empty_movie_info()
        
        # Use step-by-step parsing method for better robustness
        
        # First find all result blocks
        result_blocks = re.findall(r'<div class="result">.*?</div>\s*</div>', html_content, re.DOTALL)
        
        # Iterate through each result block to find the first valid movie result
        for result_block in result_blocks:
            # Check if contains movie marker and rating
            if '[电影]' in result_block and 'rating_nums' in result_block:
                # Extract title
                title_pattern = r'<h3>\s*<span>\[电影\]</span>\s*&nbsp;<a[^>]*>([^<]+)</a>'
                title_match = re.search(title_pattern, result_block)
                if title_match:
                    movie_info['title'] = title_match.group(1).strip()

                # Extract Douban movie ID (sid)
                sid_pattern = r'sid:\s*(\d+)'
                sid_match = re.search(sid_pattern, result_block)
                if sid_match:
                    movie_info['sid'] = sid_match.group(1)


                # Extract rating
                rating_pattern = r'<span[^>]*class="rating_nums"[^>]*>([\d.]+)</span>'
                rating_match = re.search(rating_pattern, result_block)
                if rating_match:
                    movie_info['rating'] = rating_match.group(1)
                
                # Extract review count
                review_pattern = r'<span>\((\d+)人评价\)</span>'
                review_match = re.search(review_pattern, result_block)
                if review_match:
                    movie_info['review_count'] = review_match.group(1)
                
                # Extract original title
                original_title_pattern = r'原名:([^/]+)'
                original_match = re.search(original_title_pattern, result_block)
                if original_match:
                    movie_info['original_title'] = original_match.group(1).strip()
                
                # Extract subject-cast information
                cast_pattern = r'<span[^>]*class="subject-cast"[^>]*>(.*?)</span>'
                cast_match = re.search(cast_pattern, result_block, re.DOTALL)
                if cast_match:
                    cast_text = re.sub(r'<.*?>', '', cast_match.group(1)).strip()
                    
                    # Extract year
                    year_matches = re.findall(r'(\d{4})', cast_text)
                    if year_matches:
                        movie_info['year'] = year_matches[-1]
                    
                    # Parse directors and actors
                    # Format: "原名:xxx / Director / Actor1 / Actor2 / Year"
                    clean_cast = re.sub(r'^原名:[^/]*/', '', cast_text).strip()
                    parts = [part.strip() for part in clean_cast.split('/') if part.strip()]
                    
                    if len(parts) >= 2:
                        # First is director
                        movie_info['directors'] = [parts[0]]
                        # Others are actors (excluding year)
                        actors = []
                        for part in parts[1:]:
                            if not re.match(r'^\d{4}$', part):
                                actors.append(part)
                            else:
                                break
                        movie_info['actors'] = actors[:5]
                
                # Extract description
                desc_pattern = r'<p[^>]*>(.*?)</p>'
                desc_match = re.search(desc_pattern, result_block, re.DOTALL)
                if desc_match:
                    desc_text = re.sub(r'<.*?>', '', desc_match.group(1)).strip()
                    movie_info['description'] = desc_text[:200]
                
                # Exit loop when first valid result is found
                break
        
        # Fallback solution: if no structured first result is found
        if not movie_info['title']:
            # Find all possible movie titles
            all_titles_pattern = r'<h3>\s*<span>\[电影\]</span>\s*&nbsp;<a[^>]*href="[^"]*?">([^<]+?)</a>'
            all_titles = re.findall(all_titles_pattern, html_content, re.DOTALL)
            if all_titles:
                movie_info['title'] = all_titles[0].strip()  # Take first movie title
            
            # If still no title, use looser matching
            if not movie_info['title']:
                simple_title_pattern = r'<a[^>]*>([^<>]{2,50}?)</a>'
                simple_matches = re.findall(simple_title_pattern, html_content)
                for title_text in simple_matches:
                    title_text = title_text.strip()
                    # Filter out content that's obviously not movie titles
                    if title_text and not any(keyword in title_text for keyword in ['可播放', '预告', '花絮', '回顶部', '↑', '&#8593;']):
                        movie_info['title'] = title_text
                        break
        
        return movie_info
        
    except Exception as e:
        logger.error(f"✗ Error parsing HTML: {e}")
        return _create_empty_movie_info(f'Parsing error: {str(e)}')