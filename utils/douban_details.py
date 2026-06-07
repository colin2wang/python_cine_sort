import re
import html
from typing import Optional, Dict, List, Any

import requests

from utils.common_util import bypass_douban_verification
from utils.logging_config import setup_logger

# Get logger
logger = setup_logger(__name__)


class DoubanMovieDetailsParser:
    """Parser for Douban movie details page HTML content."""

    def __init__(self, html_content: str):
        """
        Initialize parser with HTML content.
        
        Args:
            html_content (str): Raw HTML content from Douban movie page
        """
        self.html = html_content
        self.movie_details: Dict[str, Any] = {}

    def _extract_single(self, pattern: str, default: Optional[str] = None) -> Optional[str]:
        """Extract a single match using regex pattern.
        
        Args:
            pattern (str): Regex pattern to search for
            default (Optional[str]): Default value if no match found
            
        Returns:
            Optional[str]: Extracted text or default value
        """
        import re
        match = re.search(pattern, self.html)
        return match.group(1).strip() if match else default

    def _extract_multiple(self, pattern: str) -> List[str]:
        """Extract all matches using regex pattern.
        
        Args:
            pattern (str): Regex pattern to search for
            
        Returns:
            List[str]: List of extracted text values
        """
        import re
        matches = re.findall(pattern, self.html)
        return [match.strip() for match in matches]

    def _extract_directors(self) -> None:
        """Extract director information from HTML."""
        pattern = r'导演:</span>.*?<a[^>]*>([^<]+)</a>'
        directors = self._extract_multiple(pattern)
        if directors:
            self.movie_details['directors'] = [d.strip() for d in directors]

    def _extract_actors(self) -> None:
        """Extract actor information from HTML (max 10 actors)."""
        pattern = r'主演:</span>.*?<a[^>]*>([^<]+)</a>'
        actors = self._extract_multiple(pattern)
        if actors:
            self.movie_details['actors'] = [a.strip() for a in actors[:10]]

    def _extract_genres(self) -> None:
        """Extract movie genres from HTML."""
        pattern = r'<span property="v:genre">([^<]+)</span>'
        genres = self._extract_multiple(pattern)
        if genres:
            self.movie_details['genres'] = [g.strip() for g in genres]

    def _extract_description(self) -> None:
        """Extract movie description with multi-level fallback strategy.
        
        Strategy priority:
        1. Full version summary (class="all hidden")
        2. Short version summary
        3. Meta tag description
        4. JSON-LD description
        """
        import re
        
        # Level 1: Full version plot summary
        desc_pattern = r'<span property="v:summary" class="all hidden">\s*(.*?)\s*</span>'
        match = re.search(desc_pattern, self.html, re.DOTALL)
        if match:
            self.movie_details['description'] = self._clean_html(match.group(1))
            return
        
        # Level 2: Short version plot summary
        desc_pattern = r'<span property="v:summary">\s*(.*?)\s*(?:<br />|</span>)'
        match = re.search(desc_pattern, self.html, re.DOTALL)
        if match:
            self.movie_details['description'] = self._clean_html(match.group(1))
            return
        
        # Level 3: Meta tag description
        desc_pattern = r'<meta name="description" content="([^">]+)"'
        match = re.search(desc_pattern, self.html)
        if match:
            self.movie_details['description'] = match.group(1).strip()
            return
        
        # Level 4: JSON-LD description
        json_desc_pattern = r'"description":\s*"([^"]+)"'
        match = re.search(json_desc_pattern, self.html)
        if match:
            self.movie_details['description'] = match.group(1).strip()

    def _extract_english_title(self) -> None:
        """Extract English/original title from aliases."""
        import re
        
        pattern = r'又名:</span>([^<]+)'
        match = re.search(pattern, self.html)
        if not match:
            return
        
        full_aliases = match.group(1).strip()
        self.movie_details['aliases'] = full_aliases
        
        # Split by common separators and find English-only part
        parts = [p.strip() for p in full_aliases.split('/') if p.strip()]
        
        for part in parts:
            # Check if part is primarily English (no Chinese characters)
            if not re.search(r'[\u4e00-\u9fff]', part):
                self.movie_details['original_title'] = part
                return
        
        # Fallback: extract English text from first part
        if parts:
            first_part = parts[0]
            english_title = re.sub(
                r'[(（][^)）]*[一-鿿][^)）]*[)）]', '', first_part
            ).strip()
            
            # If still contains Chinese, extract only English characters
            if re.search(r'[\u4e00-\u9fff]', english_title):
                english_title = re.sub(
                    r'[^a-zA-Z0-9\s.\-]', '', first_part
                ).strip()
            
            self.movie_details['original_title'] = english_title

    def _extract_rating_distribution(self) -> None:
        """Extract rating distribution by star level."""
        pattern = r'<span class="rating_per">([\d.]+)%</span>'
        matches = re.findall(pattern, self.html)
        
        if len(matches) >= 5:
            self.movie_details['rating_distribution'] = {
                '5_star': float(matches[0]),
                '4_star': float(matches[1]),
                '3_star': float(matches[2]),
                '2_star': float(matches[3]),
                '1_star': float(matches[4])
            }

    def _extract_awards(self) -> None:
        """Extract award information from HTML."""
        pattern = r'<ul class="award">.*?<li>(.*?)</li>.*?<li>(.*?)</li>.*?<li>(.*?)</li>'
        matches = re.findall(pattern, self.html, re.DOTALL)
        
        awards = []
        for match in matches:
            if len(match) >= 3:
                award_info = {
                    'event': self._clean_html(match[0]),
                    'category': self._clean_html(match[1]),
                    'recipient': self._clean_html(match[2])
                }
                if any(award_info.values()):
                    awards.append(award_info)
        
        if awards:
            self.movie_details['awards'] = awards

    def _extract_similar_movies(self) -> None:
        """Extract similar movie recommendations (max 10)."""
        pattern = r'<a href="https://movie\.douban\.com/subject/(\d+)/[^>]*>.*?<img src="[^"]+" alt="([^"]+)" />.*?<span class="subject-rate">([\d.]+)</span>'
        matches = re.findall(pattern, self.html, re.DOTALL)
        
        similar_movies = []
        for sid, title, rating in matches[:10]:
            similar_movies.append({
                'sid': sid,
                'title': title.strip(),
                'rating': float(rating)
            })
        
        if similar_movies:
            self.movie_details['similar_movies'] = similar_movies

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags and decode entities from text.
        
        Args:
            text (str): Text potentially containing HTML
            
        Returns:
            str: Cleaned text with HTML removed
        """
        import re
        
        if not text:
            return ""
        
        # Remove all HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Decode common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&': '&',
            '<': '<',
            '>': '>',
            '"': '"',
            '&#39;': "'"
        }
        
        for entity, char in html_entities.items():
            clean_text = clean_text.replace(entity, char)
        
        # Clean up extra whitespace
        return ' '.join(clean_text.split()).strip()

    def parse(self) -> Dict[str, Any]:
        """
        Parse all movie details from HTML content.
        
        Returns:
            Dict[str, Any]: Dictionary containing extracted movie information
        """
        if not self.html:
            logger.error("HTML content is empty or None")
            return {}

        try:
            # Basic movie information
            title = self._extract_single(r'<span property="v:itemreviewed">([^<]+)</span>')
            if title:
                self.movie_details['title'] = html.unescape(title)
            
            rating = self._extract_single(
                r'<strong class="ll rating_num" property="v:average">([\d.]+)</strong>'
            )
            if rating:
                self.movie_details['rating'] = rating
            
            year = self._extract_single(r'<span class="year">\((\d{4})\)</span>')
            if year:
                self.movie_details['year'] = year
            
            # Extract lists of items
            self._extract_directors()
            self._extract_actors()
            self._extract_genres()
            
            # Extract description with fallback strategy
            self._extract_description()
            
            # Extract English/original title
            self._extract_english_title()
            
            # Enhanced information extraction
            country = self._extract_single(r'制片国家/地区:</span>([^<]+)')
            if country:
                self.movie_details['country'] = country
            
            language = self._extract_single(r'语言:</span>([^<]+)')
            if language:
                self.movie_details['language'] = language
            
            # Extract release dates
            release_dates = self._extract_multiple(
                r'<span property="v:initialReleaseDate"[^>]*>([^<]+)</span>'
            )
            if release_dates:
                self.movie_details['release_dates'] = [d.strip() for d in release_dates]
            
            # Extract runtime
            runtime = self._extract_single(r'<span property="v:runtime"[^>]*>(\d+)')
            if runtime:
                self.movie_details['runtime'] = int(runtime)
            
            # Extract IMDb ID
            imdb_id = self._extract_single(r'IMDb:</span>([^<\s]+)')
            if imdb_id:
                self.movie_details['imdb_id'] = imdb_id
            
            # Extract rating count
            rating_count = self._extract_single(
                r'<span property="v:votes">(\d+)</span>'
            )
            if rating_count:
                self.movie_details['rating_count'] = int(rating_count)
            
            # Extract rating distribution
            self._extract_rating_distribution()
            
            # Extract poster URL
            poster_url = self._extract_single(
                r'<img[^>]+src="([^"]+)"[^>]*title="点击看更多海报"'
            )
            if poster_url:
                self.movie_details['poster_url'] = poster_url
            
            # Extract awards information
            self._extract_awards()
            
            # Extract similar movies recommendation
            self._extract_similar_movies()
            
            # Extract comment/review counts
            short_comments = self._extract_single(
                r'<a href="https://movie\.douban\.com/subject/\d+/comments[^>]*>全部 (\d+) 条</a>'
            )
            if short_comments:
                self.movie_details['short_comments_count'] = int(short_comments)
            
            reviews = self._extract_single(r'<a href="reviews">全部 (\d+) 条</a>')
            if reviews:
                self.movie_details['reviews_count'] = int(reviews)
            
            # Extract Top250 ranking
            top250_rank = self._extract_single(
                r'<div class="top250"><span class="top250-no">No\.(\d+)</span>'
            )
            if top250_rank:
                self.movie_details['top250_rank'] = int(top250_rank)
            
            title_display = self.movie_details.get('title', 'Unknown')
            logger.info(f"Successfully parsed movie details: {title_display}")
            return self.movie_details
            
        except Exception as e:
            logger.error(f"Error parsing movie details: {e}")
            return {}


def get_movie_details_html(sid: str) -> Optional[str]:
    """
    Get Douban movie details page HTML content with automatic verification handling.
    
    Args:
        sid (str): Movie SID identifier
        
    Returns:
        Optional[str]: HTML response content as string, or None on failure
    """
    url = f'https://movie.douban.com/subject/{sid}/'
    
    try:
        logger.info(f"Getting movie details for SID: {sid}")
        response = bypass_douban_verification(url)
        response.encoding = 'utf-8'
        
        logger.info(f"Successfully retrieved Douban movie details: {sid}")
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


def parse_movie_details_result(html_content: str) -> Dict[str, Any]:
    """
    Parse Douban movie details page HTML content.
    
    Args:
        html_content (str): Raw HTML content from Douban movie page
        
    Returns:
        Dict[str, Any]: Dictionary containing extracted movie information including:
            - title (str): Movie title in Chinese
            - rating (str): Average rating score
            - year (str): Release year
            - directors (list): List of director names
            - actors (list): List of actor names (max 10)
            - genres (list): List of movie genres
            - description (str): Movie plot summary
            - original_title (str): Original title in other languages
            - country (str): Production country/region
            - language (str): Movie language(s)
            - release_dates (list): Release dates in different regions
            - runtime (int): Runtime in minutes
            - imdb_id (str): IMDb identifier
            - rating_count (int): Number of ratings
            - rating_distribution (dict): Rating distribution by star level
            - poster_url (str): Movie poster image URL
            - awards (list): List of award information
            - similar_movies (list): Similar movie recommendations
            - short_comments_count (int): Number of short comments
            - reviews_count (int): Number of detailed reviews
            - top250_rank (int): Douban Top 250 ranking
    """
    parser = DoubanMovieDetailsParser(html_content)
    return parser.parse()