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
        dict: Parsed movie information including enhanced details
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
            movie_details['actors'] = [actor.strip() for actor in actor_matches[:10]]  # Take first 10
        
        # Extract genres
        genre_pattern = r'<span property="v:genre">([^<]+)</span>'
        genre_matches = re.findall(genre_pattern, html_content)
        if genre_matches:
            movie_details['genres'] = [genre.strip() for genre in genre_matches]
        
        # Extract description - 多级降级提取策略
        # 第一级：提取完整版剧情简介（class="all hidden"）
        desc_pattern1 = r'<span property="v:summary" class="all hidden">\s*(.*?)\s*</span>'
        desc_match1 = re.search(desc_pattern1, html_content, re.DOTALL)
        if desc_match1:
            description = desc_match1.group(1).strip()
            # 清理HTML标签和多余空白
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\s+', ' ', description).strip()
            if description:
                movie_details['description'] = description
        else:
            # 第二级：提取简短版剧情简介
            desc_pattern2 = r'<span property="v:summary">\s*(.*?)\s*(?:<br />|</span>)'
            desc_match2 = re.search(desc_pattern2, html_content, re.DOTALL)
            if desc_match2:
                description = desc_match2.group(1).strip()
                # 清理HTML标签和多余空白
                description = re.sub(r'<[^>]+>', '', description)
                description = re.sub(r'\s+', ' ', description).strip()
                if description:
                    movie_details['description'] = description
            else:
                # 第三级：从meta标签提取description
                meta_desc_pattern = r'<meta name="description" content="([^">]+)"'
                meta_desc_match = re.search(meta_desc_pattern, html_content)
                if meta_desc_match:
                    movie_details['description'] = meta_desc_match.group(1).strip()
                else:
                    # 第四级：从JSON-LD中提取description
                    json_desc_pattern = r'"description": "([^"]+)"'
                    json_desc_match = re.search(json_desc_pattern, html_content)
                    if json_desc_match:
                        movie_details['description'] = json_desc_match.group(1).strip()
        
        # Extract original title
        original_title_pattern = r'又名:</span>([^<]+)'
        original_title_match = re.search(original_title_pattern, html_content)
        if original_title_match:
            movie_details['original_title'] = original_title_match.group(1).strip()
        
        # ============ Enhanced Information Extraction ============
        
        # Extract country/region
        country_pattern = r'制片国家/地区:</span>([^<]+)'
        country_match = re.search(country_pattern, html_content)
        if country_match:
            movie_details['country'] = country_match.group(1).strip()
        
        # Extract language
        language_pattern = r'语言:</span>([^<]+)'
        language_match = re.search(language_pattern, html_content)
        if language_match:
            movie_details['language'] = language_match.group(1).strip()
        
        # Extract release dates
        release_date_pattern = r'<span property="v:initialReleaseDate"[^>]*>([^<]+)</span>'
        release_dates = re.findall(release_date_pattern, html_content)
        if release_dates:
            movie_details['release_dates'] = [date.strip() for date in release_dates]
        
        # Extract runtime
        runtime_pattern = r'<span property="v:runtime"[^>]*>(\d+)'
        runtime_match = re.search(runtime_pattern, html_content)
        if runtime_match:
            movie_details['runtime'] = int(runtime_match.group(1))
        
        # Extract IMDb ID
        imdb_pattern = r'IMDb:</span>([^<\s]+)'
        imdb_match = re.search(imdb_pattern, html_content)
        if imdb_match:
            movie_details['imdb_id'] = imdb_match.group(1).strip()
        
        # Extract rating count
        rating_count_pattern = r'<span property="v:votes">(\d+)</span>'
        rating_count_match = re.search(rating_count_pattern, html_content)
        if rating_count_match:
            movie_details['rating_count'] = int(rating_count_match.group(1))
        
        # Extract rating distribution
        rating_dist_pattern = r'<span class="rating_per">([\d.]+)%</span>'
        rating_dist_matches = re.findall(rating_dist_pattern, html_content)
        if len(rating_dist_matches) >= 5:
            movie_details['rating_distribution'] = {
                '5_star': float(rating_dist_matches[0]),
                '4_star': float(rating_dist_matches[1]),
                '3_star': float(rating_dist_matches[2]),
                '2_star': float(rating_dist_matches[3]),
                '1_star': float(rating_dist_matches[4])
            }
        
        # Extract poster image URL
        poster_pattern = r'<img src="([^"]+)"[^>]*title="点击看更多海报"'
        poster_match = re.search(poster_pattern, html_content)
        if poster_match:
            movie_details['poster_url'] = poster_match.group(1).strip()
        
        # Extract awards information
        award_pattern = r'<ul class="award">.*?<li>(.*?)</li>.*?<li>(.*?)</li>.*?<li>(.*?)</li>'
        award_matches = re.findall(award_pattern, html_content, re.DOTALL)
        if award_matches:
            awards = []
            for match in award_matches:
                award_info = {
                    'event': match[0].strip() if match[0].strip() else '',
                    'category': match[1].strip() if match[1].strip() else '',
                    'recipient': match[2].strip() if match[2].strip() else ''
                }
                if any(award_info.values()):
                    awards.append(award_info)
            if awards:
                movie_details['awards'] = awards
        
        # Extract similar movies recommendation
        similar_pattern = r'<a href="https://movie.douban.com/subject/(\d+)/[^>]*>.*?<img src="[^"]+" alt="([^"]+)" />.*?<span class="subject-rate">([\d.]+)</span>'
        similar_matches = re.findall(similar_pattern, html_content, re.DOTALL)
        if similar_matches:
            similar_movies = []
            for sid, title, rating in similar_matches[:10]:  # Top 10 similar movies
                similar_movies.append({
                    'sid': sid,
                    'title': title.strip(),
                    'rating': float(rating)
                })
            movie_details['similar_movies'] = similar_movies
        
        # Extract short comments count
        short_comments_pattern = r'<a href="https://movie.douban.com/subject/\d+/comments[^>]*>全部 (\d+) 条</a>'
        short_comments_match = re.search(short_comments_pattern, html_content)
        if short_comments_match:
            movie_details['short_comments_count'] = int(short_comments_match.group(1))
        
        # Extract reviews count
        reviews_pattern = r'<a href="reviews">全部 (\d+) 条</a>'
        reviews_match = re.search(reviews_pattern, html_content)
        if reviews_match:
            movie_details['reviews_count'] = int(reviews_match.group(1))
        
        # Extract Top250 ranking if exists
        top250_pattern = r'<div class="top250"><span class="top250-no">No.(\d+)</span>'
        top250_match = re.search(top250_pattern, html_content)
        if top250_match:
            movie_details['top250_rank'] = int(top250_match.group(1))
        
        logger.info(f"✓ Successfully parsed movie details: {movie_details.get('title', 'Unknown')}")
        return movie_details
        
    except Exception as e:
        logger.error(f"✗ Error parsing movie details: {e}")
        return {}