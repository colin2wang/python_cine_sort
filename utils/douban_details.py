import requests
from typing import Optional

from utils import get_default_logger
from utils.common_util import sleep_for_random_time

# 获取默认日志记录器
logger = get_default_logger()


def get_movie_details_html(sid: str) -> Optional[str]:
    """获取豆瓣电影搜索结果

    Args:
        sid (str): 电影SID

    Returns:
        Optional[str]: HTML响应内容，失败时返回None
    """
    # 构建搜索URL
    url = f'https://movie.douban.com/subject/{sid}/'

    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        # 发送GET请求
        logger.info(f"GET {url}")
        sleep_for_random_time()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查HTTP状态码

        # 设置正确的编码
        response.encoding = 'utf-8'

        logger.info(f"✓ 成功获取豆瓣电影详情: {sid}")
        return response.text

    except requests.exceptions.Timeout:
        logger.warning(f"✗ 请求超时: {sid}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ 连接错误: {sid}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"✗ HTTP错误 {e.response.status_code}: {sid}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ 请求异常: {e} - {sid}")
        return None
    except Exception as e:
        logger.error(f"✗ 未知错误: {e} - {sid}")
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