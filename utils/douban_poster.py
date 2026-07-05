import os
import re
from typing import Optional, Dict, List, Any

import requests

from utils.common_util import bypass_douban_verification, sleep_for_random_time
from utils.logging_config import setup_logger

logger = setup_logger(__name__)


class DoubanPosterParser:
    """Parser for Douban movie photos/poster page HTML content."""

    def __init__(self, html_content: str):
        self.html = html_content
        self.posters: List[Dict[str, str]] = []

    def parse(self) -> List[Dict[str, str]]:
        """
        Parse poster image URLs from the photos page HTML.

        Returns:
            List[Dict[str, str]]: List of poster info dicts with keys:
                - thumbnail: thumbnail image URL
                - original: original image URL (if available)
                - title: image title/description (e.g., "正式海报 中国大陆")
        """
        if not self.html:
            logger.error("HTML content is empty or None")
            return []

        try:
            # Pattern 1: Match <li> structure with <div class="cover"> and <div class="name">
            # <li data-id="...">...<div class="cover">...<img src="..." />...</div>...<div class="name">TITLE...</div>...</li>
            pattern = r'<li[^>]*>.*?<div class="cover">.*?<img[^>]+(?:src|data-img)="([^"]+)".*?</div>.*?<div class="name">\s*(.*?)\s*<a'
            matches = re.findall(pattern, self.html, re.DOTALL)

            for img_url, title_raw in matches:
                # Clean title: remove HTML tags and extra whitespace
                title = re.sub(r'<[^>]+>', '', title_raw).strip()
                # Remove trailing comment count like "9回应"
                title = re.sub(r'\d+回应$', '', title).strip()

                poster_info = {
                    'thumbnail': img_url,
                    'original': self._get_original_url(img_url),
                    'title': title
                }
                self.posters.append(poster_info)

            # Pattern 2: Fallback - match <li> with <div class="name"> without <a> tag requirement
            if not self.posters:
                pattern = r'<li[^>]*>.*?<div class="cover">.*?<img[^>]+(?:src|data-img)="([^"]+)".*?</div>.*?<div class="name">\s*(.*?)\s*</div>'
                matches = re.findall(pattern, self.html, re.DOTALL)

                for img_url, title_raw in matches:
                    title = re.sub(r'<[^>]+>', '', title_raw).strip()
                    title = re.sub(r'\d+回应$', '', title).strip()

                    poster_info = {
                        'thumbnail': img_url,
                        'original': self._get_original_url(img_url),
                        'title': title
                    }
                    self.posters.append(poster_info)

            # Pattern 3: Simpler img + alt fallback
            if not self.posters:
                pattern = r'<img[^>]+(?:src|data-img)="([^"]+)"[^>]*(?:alt="([^"]*)")?[^>]*/>'
                matches = re.findall(pattern, self.html)
                for img_url, alt in matches:
                    if 'doubanio.com' in img_url:
                        poster_info = {
                            'thumbnail': img_url,
                            'original': self._get_original_url(img_url),
                            'title': alt.strip() if alt else ''
                        }
                        self.posters.append(poster_info)

            logger.info(f"Found {len(self.posters)} poster images")
            return self.posters

        except Exception as e:
            logger.error(f"Error parsing poster page: {e}")
            return []

    @staticmethod
    def _get_original_url(thumbnail_url: str) -> str:
        """
        Convert thumbnail URL to original image URL.
        Douban uses various path patterns:
        - /view/photo/m/public/p123.webp -> /view/photo/l/public/p123.webp
        - /view/photo/s_ratio_poster/public/p123.jpg -> /view/photo/l/public/p123.jpg
        - /view/photo/m_ratio_poster/public/p123.jpg -> /view/photo/l/public/p123.jpg

        Args:
            thumbnail_url: The thumbnail image URL

        Returns:
            str: Original image URL
        """
        if not thumbnail_url:
            return thumbnail_url

        # Replace path variants to get original (largest) version
        # Handle /m/ (medium) -> /l/ (large)
        original = re.sub(r'/view/photo/m/', '/view/photo/l/', thumbnail_url)
        # Handle ratio poster variants
        original = re.sub(r'/s_ratio_poster/', '/l/', original)
        original = re.sub(r'/m_ratio_poster/', '/l/', original)
        original = re.sub(r'/r_ratio_poster/', '/l/', original)

        # Ensure HTTPS
        if original.startswith('//'):
            original = 'https:' + original
        elif original.startswith('http://'):
            original = original.replace('http://', 'https://', 1)

        return original


def get_posters_page_html(sid: str, photo_type: str = 'R') -> Optional[str]:
    """
    Get Douban movie photos page HTML content.

    Args:
        sid (str): Movie SID identifier
        photo_type (str): Photo type filter. Common values:
            - 'R': 海报 (Poster)
            - 'S': 剧照 (Still)
            - 'W': 工作照 (Behind the scenes)
            - 'N': 获奖 (Awards)
            - 'G': 花絮 (Trivia)

    Returns:
        Optional[str]: HTML response content as string, or None on failure
    """
    url = f'https://movie.douban.com/subject/{sid}/photos?type={photo_type}'

    try:
        logger.info(f"Getting posters for SID: {sid}, type: {photo_type}")
        response = bypass_douban_verification(url)
        response.encoding = 'utf-8'

        logger.info(f"Successfully retrieved Douban photos page: {sid}")
        return response.text

    except requests.exceptions.Timeout:
        logger.warning(f"Request timeout: {sid}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error: {sid}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code}: {sid}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {e} - {sid}")
        return None
    except Exception as e:
        logger.error(f"Unknown error: {e} - {sid}")
        return None


def parse_posters_result(html_content: str) -> List[Dict[str, str]]:
    """
    Parse Douban movie photos page HTML content.

    Args:
        html_content (str): Raw HTML content from Douban photos page

    Returns:
        List[Dict[str, str]]: List of poster info dicts
    """
    parser = DoubanPosterParser(html_content)
    return parser.parse()


def download_poster(url: str, save_path: str) -> bool:
    """
    Download a poster image to local file.

    Args:
        url (str): Image URL to download
        save_path (str): Local file path to save the image

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://movie.douban.com/'
        }

        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded poster to: {save_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to download poster {url}: {e}")
        return False


def get_movie_poster(sid: str, save_dir: str = None) -> Optional[str]:
    """
    Get and download the first poster image for a movie.

    Args:
        sid (str): Movie SID identifier
        save_dir (str): Directory to save the poster. If None, uses current directory.

    Returns:
        Optional[str]: Path to downloaded poster file, or None on failure
    """
    html_content = get_posters_page_html(sid, photo_type='R')
    if not html_content:
        return None

    posters = parse_posters_result(html_content)
    if not posters:
        logger.warning(f"No posters found for SID: {sid}")
        return None

    # Download the first poster
    poster = posters[0]
    original_url = poster['original']

    if save_dir is None:
        save_dir = os.getcwd()

    # Extract filename from URL
    filename = original_url.split('/')[-1]
    if not filename or '.' not in filename:
        filename = f"poster_{sid}.jpg"

    save_path = os.path.join(save_dir, filename)

    if download_poster(original_url, save_path):
        return save_path

    return None


def get_all_movie_posters(sid: str, save_dir: str = None, max_count: int = 10) -> List[str]:
    """
    Get and download multiple poster images for a movie.

    Args:
        sid (str): Movie SID identifier
        save_dir (str): Directory to save posters. If None, uses current directory.
        max_count (int): Maximum number of posters to download

    Returns:
        List[str]: List of paths to downloaded poster files
    """
    html_content = get_posters_page_html(sid, photo_type='R')
    if not html_content:
        return []

    posters = parse_posters_result(html_content)
    if not posters:
        logger.warning(f"No posters found for SID: {sid}")
        return []

    if save_dir is None:
        save_dir = os.getcwd()

    downloaded = []
    for i, poster in enumerate(posters[:max_count]):
        sleep_for_random_time()
        original_url = poster['original']

        filename = original_url.split('/')[-1]
        if not filename or '.' not in filename:
            filename = f"poster_{sid}_{i+1}.jpg"

        save_path = os.path.join(save_dir, filename)

        if download_poster(original_url, save_path):
            downloaded.append(save_path)

    logger.info(f"Downloaded {len(downloaded)} posters for SID: {sid}")
    return downloaded


def _get_image_size(url: str) -> int:
    """
    Get image file size in bytes by fetching headers.

    Args:
        url: Image URL

    Returns:
        File size in bytes, 0 if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://movie.douban.com/'
        }
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            content_length = response.headers.get('Content-Length', '0')
            return int(content_length) if content_length.isdigit() else 0
    except Exception:
        pass
    return 0


def _is_chinese_region(title: str) -> bool:
    """
    Check if title indicates a Chinese region (中国大陆, 中国香港, 中国台湾, etc.).

    Args:
        title: Poster title (e.g., "正式海报 中国大陆")

    Returns:
        True if title indicates a Chinese region
    """
    chinese_regions = [
        '中国大陆', '中国香港', '中国台湾',
        '香港', '台湾', '澳门',
        'China', 'Hong Kong', 'Taiwan'
    ]
    return any(region in title for region in chinese_regions)


def _is_chinese_text(text: str) -> bool:
    """
    Check if text contains Chinese characters.

    Args:
        text: Text to check

    Returns:
        True if text contains Chinese characters
    """
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def filter_and_sort_posters(
    posters: List[Dict[str, str]],
    title_keyword: str = "正式海报",
    prefer_chinese_region: bool = True
) -> List[Dict[str, str]]:
    """
    Filter posters by title keyword and sort by priority:
    1. Must contain title_keyword (e.g., "正式海报")
    2. Chinese region titles first (中国大陆, 中国香港, 中国台湾)
    3. Other Chinese titles
    4. Non-Chinese titles last

    Args:
        posters: List of poster info dicts
        title_keyword: Keyword to filter titles (e.g., "正式海报")
        prefer_chinese_region: If True, prioritize Chinese region posters

    Returns:
        Filtered and sorted list of poster info dicts
    """
    # Step 1: Filter by title keyword - MUST contain "正式海报"
    filtered = [p for p in posters if title_keyword in p.get('title', '')]

    # If no exact match, try partial match (e.g., "海报")
    if not filtered:
        filtered = [p for p in posters if "海报" in p.get('title', '')]

    # If still no match, use all posters
    if not filtered:
        logger.warning(f"No posters with '{title_keyword}' found, using all posters")
        filtered = posters

    # Step 2: Sort by Chinese region preference
    if prefer_chinese_region:
        # Priority 1: Chinese region (中国大陆, 中国香港, 中国台湾)
        chinese_region = [p for p in filtered if _is_chinese_region(p.get('title', ''))]
        # Priority 2: Other Chinese titles
        other_chinese = [p for p in filtered
                         if _is_chinese_text(p.get('title', ''))
                         and not _is_chinese_region(p.get('title', ''))]
        # Priority 3: Non-Chinese titles
        non_chinese = [p for p in filtered if not _is_chinese_text(p.get('title', ''))]

        filtered = chinese_region + other_chinese + non_chinese

        if chinese_region:
            logger.info(f"Found {len(chinese_region)} Chinese region posters")
        if other_chinese:
            logger.info(f"Found {len(other_chinese)} other Chinese posters")

    # Step 3: Get sizes and sort by size (largest first)
    logger.info("Checking poster sizes...")
    for poster in filtered:
        poster['size'] = _get_image_size(poster['original'])
        sleep_for_random_time()

    # Sort by size descending
    filtered.sort(key=lambda x: x.get('size', 0), reverse=True)

    return filtered


def get_official_posters(
    sid: str,
    title_keyword: str = "正式海报"
) -> List[Dict[str, Any]]:
    """
    Get official poster metadata: top 3 largest + 1 Chinese poster.
    Does not download, only returns the filtered/sorted poster info.

    Args:
        sid: Movie SID identifier
        title_keyword: Keyword to filter poster titles

    Returns:
        List of poster info dicts with size, title, original URL, etc.
    """
    html_content = get_posters_page_html(sid, photo_type='R')
    if not html_content:
        return []

    posters = parse_posters_result(html_content)
    if not posters:
        return []

    # Filter by keyword
    filtered = [p for p in posters if title_keyword in p.get('title', '')]
    if not filtered:
        filtered = [p for p in posters if "海报" in p.get('title', '')]
    if not filtered:
        filtered = posters

    # Get sizes and sort by size (largest first)
    for poster in filtered:
        poster['size'] = _get_image_size(poster['original'])
        sleep_for_random_time()

    filtered.sort(key=lambda x: x.get('size', 0), reverse=True)

    # Select top 3 by size
    top_by_size = filtered[:3]

    # Find Chinese poster (not already in top 3)
    chinese_poster = None
    for poster in filtered:
        if poster not in top_by_size and _is_chinese_text(poster.get('title', '')):
            chinese_poster = poster
            break

    selected = list(top_by_size)
    if chinese_poster:
        selected.append(chinese_poster)

    return selected


def download_official_posters(
    sid: str,
    save_dir: str,
    title_keyword: str = "正式海报"
) -> List[str]:
    """
    Download official posters: top 3 largest + 1 Chinese poster.

    Selection logic:
    1. Filter posters containing title_keyword (default: "正式海报")
    2. Sort all by file size (largest first)
    3. Select top 3 by size
    4. Add 1 Chinese poster if available and not already in top 3
    5. Handle edge cases: no Chinese, less than 3 posters, etc.

    Args:
        sid: Movie SID identifier
        save_dir: Directory to save posters
        title_keyword: Keyword to filter poster titles

    Returns:
        List of paths to downloaded poster files
    """
    html_content = get_posters_page_html(sid, photo_type='R')
    if not html_content:
        return []

    posters = parse_posters_result(html_content)
    if not posters:
        logger.warning(f"No posters found for SID: {sid}")
        return []

    # Filter by keyword
    filtered = [p for p in posters if title_keyword in p.get('title', '')]
    if not filtered:
        filtered = [p for p in posters if "海报" in p.get('title', '')]
    if not filtered:
        logger.warning(f"No posters with '{title_keyword}' found, using all posters")
        filtered = posters

    # Get sizes and sort by size (largest first)
    logger.info("Checking poster sizes...")
    for poster in filtered:
        poster['size'] = _get_image_size(poster['original'])
        sleep_for_random_time()

    filtered.sort(key=lambda x: x.get('size', 0), reverse=True)

    # Select top 3 by size
    top_by_size = filtered[:3]

    # Find Chinese poster (not already in top 3)
    chinese_poster = None
    for poster in filtered:
        if poster not in top_by_size and _is_chinese_text(poster.get('title', '')):
            chinese_poster = poster
            break

    # Build final selection: top 3 + 1 Chinese (if available)
    selected = list(top_by_size)
    if chinese_poster:
        selected.append(chinese_poster)

    if not selected:
        logger.warning(f"No suitable posters found for SID: {sid}")
        return []

    os.makedirs(save_dir, exist_ok=True)

    downloaded = []
    for i, poster in enumerate(selected):
        sleep_for_random_time()
        original_url = poster['original']
        title = poster.get('title', '')
        size = poster.get('size', 0)

        # Generate filename: p{image_id}_{keyword}_{region}.{ext} or p{image_id}_{keyword}.{ext}
        # Extract base name and extension from URL (e.g., "p1082990842.webp" -> "p1082990842", "webp")
        url_filename = original_url.split('/')[-1]
        if '.' in url_filename:
            base_name, ext = url_filename.rsplit('.', 1)
            ext = f".{ext}"
        else:
            base_name = url_filename
            ext = ".jpg"

        # Parse title to get keyword and region
        # Title format: "正式海报 中国大陆" or "正式海报 美国" or "正式海报"
        title_parts = title.strip().split()
        keyword = title_parts[0] if title_parts else "正式海报"
        region = title_parts[1] if len(title_parts) > 1 else ""

        # Build filename
        if region:
            filename = f"{base_name}_{keyword}_{region}{ext}"
        else:
            filename = f"{base_name}_{keyword}{ext}"

        save_path = os.path.join(save_dir, filename)

        logger.info(f"Downloading poster {i+1}/{len(selected)}: {title} ({size/1024:.1f}KB)")
        if download_poster(original_url, save_path):
            downloaded.append(save_path)

    logger.info(f"Downloaded {len(downloaded)} official posters for SID: {sid}")
    return downloaded
