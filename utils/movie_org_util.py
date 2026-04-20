"""Movie organization utility module

Used to organize movie files into structured directories with metadata files

filename: movie_org_util.py
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

import yaml

from .logging_config import setup_logger

logger = setup_logger(__name__)


@dataclass
class MovieOrgConfig:
    """Movie organizer configuration class"""

    movie_folder: str = "I:/我的电影/已整理"
    directory_format: str = "{chinese_title}.{english_title}.{year}"
    file_encoding: str = "utf-8"
    create_rating_file: bool = True
    create_sid_file: bool = True

    def __init__(self, config_file: Optional[Path] = None):
        if config_file and config_file.exists():
            self.load_config(config_file)
        elif config_file:
            raise ValueError(f"Configuration file not found: {config_file}")
        else:
            logger.warning("No configuration file provided, using default settings")

    def load_config(self, config_file: Path):
        """Load configuration from YAML configuration file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Load configuration items
            self.movie_folder = config.get('movie_folder', self.movie_folder)
            self.directory_format = config.get('directory_format', self.directory_format)
            self.file_encoding = config.get('file_encoding', self.file_encoding)
            self.create_rating_file = config.get('create_rating_file', self.create_rating_file)
            self.create_sid_file = config.get('create_sid_file', self.create_sid_file)

            logger.debug(f"✓ Configuration loaded from {config_file}")

        except Exception as e:
            logger.error(f"✗ Failed to load configuration file: {e}")
            raise


class MovieOrganizer:
    """Movie organizer - creates structured directories for movies"""

    def __init__(self, config: Optional[MovieOrgConfig] = None):
        self.config = config or MovieOrgConfig()
        self.logger = setup_logger(__name__)

    def create_movie_directory(self, movie_info: Dict) -> Optional[Path]:
        """Create movie directory structure based on movie information

        Args:
            movie_info (dict): Movie information dictionary containing:
                - title: Chinese title
                - original_title: Original/English title
                - year: Release year
                - sid: Douban movie ID
                - rating: Douban rating

        Returns:
            Optional[Path]: Created directory path, None on failure
        """
        try:
            # Validate required fields
            if not movie_info.get('title'):
                self.logger.error("✗ Movie title is required")
                return None

            # Extract movie information
            chinese_title = movie_info.get('title', '').strip()
            english_title = movie_info.get('original_title', '').strip()
            year = movie_info.get('year', '').strip()
            sid = movie_info.get('sid', '').strip()
            rating = movie_info.get('rating', '').strip()

            # Clean titles for directory naming (remove invalid characters)
            chinese_title_clean = self._clean_filename(chinese_title)
            english_title_clean = self._clean_filename(english_title) if english_title else ''
            year_clean = year if year else ''

            # Generate directory name using format template
            dir_name = self.config.directory_format.format(
                chinese_title=chinese_title_clean,
                english_title=english_title_clean,
                year=year_clean
            )

            # Remove consecutive dots and trailing dots
            dir_name = re.sub(r'\.{2,}', '.', dir_name).rstrip('.')

            if not dir_name:
                self.logger.error("✗ Generated directory name is empty")
                return None

            # Create full directory path
            base_path = Path(self.config.movie_folder)
            movie_dir = base_path / dir_name

            # Create directory (including parent directories)
            movie_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✓ Created directory: {movie_dir}")

            # Create metadata files
            if self.config.create_sid_file and sid:
                sid_file = movie_dir / f"{sid}.txt"
                self._write_text_file(sid_file, sid)
                self.logger.info(f"✓ Created SID file: {sid_file}")

            if self.config.create_rating_file and rating:
                rating_file = movie_dir / f"{rating}.txt"
                self._write_text_file(rating_file, "")
                self.logger.info(f"✓ Created rating file: {rating_file}")

            return movie_dir

        except Exception as e:
            self.logger.error(f"✗ Error creating movie directory: {e}")
            return None

    def _clean_filename(self, filename: str) -> str:
        """Clean filename by removing invalid characters

        Args:
            filename (str): Original filename

        Returns:
            str: Cleaned filename with spaces replaced by dots
        """
        if not filename:
            return ''

        # Replace invalid characters with dots
        # Windows invalid characters: < > : " / \ | ? *
        cleaned = re.sub(r'[<>:"/\\|?*]', '.', filename)

        # Replace spaces with dots for better directory naming
        cleaned = cleaned.replace(' ', '.')

        # Remove leading/trailing spaces and dots
        cleaned = cleaned.strip(' .')

        # Replace multiple consecutive dots with single dot
        cleaned = re.sub(r'\.{2,}', '.', cleaned)

        return cleaned

    def create_movie_directory_by_detail(self, movie_details: Dict) -> Optional[Path]:
        """Create movie directory structure based on Douban movie details

        Args:
            movie_details (dict): Movie details dictionary from douban_details.parse_movie_details_result,
                containing fields like:
                - title: Chinese title
                - original_title: Original/English title
                - year: Release year
                - rating: Douban rating
                - description: Movie description/plot summary
                - directors: List of directors
                - actors: List of actors
                - genres: List of genres
                - country: Country/region
                - language: Language
                - runtime: Runtime in minutes
                - imdb_id: IMDb ID
                - release_dates: List of release dates
                And other enhanced information

        Returns:
            Optional[Path]: Created directory path, None on failure
        """
        try:
            # Validate required fields
            if not movie_details.get('title'):
                self.logger.error("✗ Movie title is required")
                return None

            # Extract movie information
            chinese_title = movie_details.get('title', '').strip()
            english_title = movie_details.get('original_title', '').strip()
            year = movie_details.get('year', '').strip()
            sid = movie_details.get('sid', '').strip()
            rating = movie_details.get('rating', '').strip()
            description = movie_details.get('description', '').strip()

            # Clean titles for directory naming (remove invalid characters)
            chinese_title_clean = self._clean_filename(chinese_title)
            english_title_clean = self._clean_filename(english_title) if english_title else ''
            year_clean = year if year else ''

            # Generate directory name using format template
            dir_name = self.config.directory_format.format(
                chinese_title=chinese_title_clean,
                english_title=english_title_clean,
                year=year_clean
            )

            # Remove consecutive dots and trailing dots
            dir_name = re.sub(r'\.{2,}', '.', dir_name).rstrip('.')

            if not dir_name:
                self.logger.error("✗ Generated directory name is empty")
                return None

            # Create full directory path
            base_path = Path(self.config.movie_folder)
            movie_dir = base_path / dir_name

            # Create directory (including parent directories)
            movie_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✓ Created directory: {movie_dir}")

            # Create metadata files
            if self.config.create_rating_file and rating:
                rating_file = movie_dir / f"{rating}.txt"
                self._write_text_file(rating_file, "")
                self.logger.info(f"✓ Created rating file: {rating_file}")

            # Create sid.txt with detailed movie information
            if self.config.create_sid_file:
                sid_file = movie_dir / f"{sid}.txt" if sid else movie_dir / "sid.txt"
                sid_content = self._build_sid_content(movie_details)
                self._write_text_file(sid_file, sid_content)
                self.logger.info(f"✓ Created SID file with details: {sid_file}")

            return movie_dir

        except Exception as e:
            self.logger.error(f"✗ Error creating movie directory from details: {e}")
            return None

    def _build_sid_content(self, movie_details: Dict) -> str:
        """Build comprehensive movie information content for sid.txt file

        Args:
            movie_details (dict): Movie details dictionary from Douban

        Returns:
            str: Formatted movie information text
        """
        lines = []

        # Basic Information Section
        lines.append("=" * 50)
        lines.append("电影基本信息")
        lines.append("=" * 50)

        # Title and SID
        if movie_details.get('title'):
            lines.append(f"中文名称: {movie_details['title']}")
        if movie_details.get('original_title'):
            lines.append(f"英文原名: {movie_details['original_title']}")
        if movie_details.get('aliases'):
            lines.append(f"其他别名: {movie_details['aliases']}")
        if movie_details.get('sid'):
            lines.append(f"豆瓣ID: {movie_details['sid']}")
        if movie_details.get('year'):
            lines.append(f"年份: {movie_details['year']}")
        if movie_details.get('rating'):
            lines.append(f"豆瓣评分: {movie_details['rating']}")

        # Rating count
        if movie_details.get('rating_count'):
            lines.append(f"评分人数: {movie_details['rating_count']}")

        # Top250 ranking
        if movie_details.get('top250_rank'):
            lines.append(f"Top250排名: #{movie_details['top250_rank']}")

        lines.append("")

        if movie_details.get('directors'):
            directors = ', '.join(movie_details['directors'])
            lines.append(f"导演: {directors}")

        if movie_details.get('actors'):
            actors = ', '.join(movie_details['actors'][:10])  # Show first 10 actors
            lines.append(f"主演: {actors}")

        lines.append("")

        # Movie Details Section
        lines.append("-" * 50)
        lines.append("详细信息")
        lines.append("-" * 50)

        if movie_details.get('genres'):
            genres = ', '.join(movie_details['genres'])
            lines.append(f"类型: {genres}")

        if movie_details.get('country'):
            lines.append(f"制片国家/地区: {movie_details['country']}")

        if movie_details.get('language'):
            lines.append(f"语言: {movie_details['language']}")

        if movie_details.get('runtime'):
            lines.append(f"片长: {movie_details['runtime']}分钟")

        if movie_details.get('imdb_id'):
            lines.append(f"IMDb: {movie_details['imdb_id']}")

        if movie_details.get('release_dates'):
            release_dates = ', '.join(movie_details['release_dates'])
            lines.append(f"上映日期: {release_dates}")

        lines.append("")

        # Description Section
        lines.append("-" * 50)
        lines.append("剧情简介")
        lines.append("-" * 50)

        if movie_details.get('description'):
            lines.append(movie_details['description'])
        else:
            lines.append("暂无剧情简介")

        lines.append("")

        if movie_details.get('short_comments_count'):
            lines.append(f"短评数量: {movie_details['short_comments_count']}")

        if movie_details.get('reviews_count'):
            lines.append(f"影评数量: {movie_details['reviews_count']}")

        # Awards
        if movie_details.get('awards'):
            lines.append(f"获奖情况: 共{len(movie_details['awards'])}条记录")
            for award in movie_details['awards'][:5]:  # Show first 5 awards
                award_parts = []
                if award.get('event'):
                    award_parts.append(award['event'])
                if award.get('category'):
                    award_parts.append(award['category'])
                if award.get('recipient'):
                    award_parts.append(award['recipient'])
                if award_parts:
                    lines.append(f"  - {' / '.join(award_parts)}")

        # Similar movies
        if movie_details.get('similar_movies'):
            lines.append(f"相似推荐: 共{len(movie_details['similar_movies'])}部")
            for movie in movie_details['similar_movies'][:5]:  # Show first 5
                lines.append(f"  - {movie.get('title', 'Unknown')} (评分: {movie.get('rating', 'N/A')})")

        lines.append("")
        lines.append("=" * 50)

        return '\n'.join(lines)

    def _build_rating_content(self, movie_info: Dict) -> str:
        """Build rating content for rating file

        Args:
            movie_info (dict): Movie information dictionary

        Returns:
            str: Formatted rating information text
        """
        lines = []
        
        if movie_info.get('rating'):
            lines.append(f"豆瓣评分: {movie_info['rating']}")
        
        if movie_info.get('rating_count'):
            lines.append(f"评分人数: {movie_info['rating_count']}")
        
        if movie_info.get('top250_rank'):
            lines.append(f"Top250排名: #{movie_info['top250_rank']}")
        
        return '\n'.join(lines) if lines else movie_info.get('rating', '')

    def _build_rating_content_from_details(self, movie_details: Dict) -> str:
        """Build rating content from movie details for rating file

        Args:
            movie_details (dict): Movie details dictionary from Douban

        Returns:
            str: Formatted rating information text
        """
        lines = []
        
        if movie_details.get('rating'):
            lines.append(f"豆瓣评分: {movie_details['rating']}")
        
        if movie_details.get('rating_count'):
            lines.append(f"评分人数: {movie_details['rating_count']}")
        
        if movie_details.get('top250_rank'):
            lines.append(f"Top250排名: #{movie_details['top250_rank']}")
        
        return '\n'.join(lines) if lines else movie_details.get('rating', '')

    def _write_text_file(self, file_path: Path, content: str):
        """Write text content to file

        Args:
            file_path (Path): File path
            content (str): Content to write
        """
        with open(file_path, 'w', encoding=self.config.file_encoding) as f:
            f.write(content)


def organize_movie(
    movie_info: Dict,
    config_file: Optional[str] = None
) -> Optional[Path]:
    """Convenience function: organize a single movie

    Args:
        movie_info (dict): Movie information dictionary
        config_file (str, optional): Configuration file path

    Returns:
        Optional[Path]: Created directory path, None on failure
    """
    # Load configuration
    if config_file:
        config = MovieOrgConfig(Path(config_file))
    else:
        # Auto-detect configuration file
        config_path = Path(__file__).parent.parent / "configs" / "movie_org_util.yml"
        if config_path.exists():
            config = MovieOrgConfig(config_path)
        else:
            config = MovieOrgConfig()

    # Create organizer and process
    organizer = MovieOrganizer(config)
    return organizer.create_movie_directory(movie_info)


def organize_movie_by_detail(
    movie_details: Dict,
    config_file: Optional[str] = None
) -> Optional[Path]:
    """Convenience function: organize a single movie using Douban details

    Args:
        movie_details (dict): Movie details dictionary from douban_details.parse_movie_details_result
        config_file (str, optional): Configuration file path

    Returns:
        Optional[Path]: Created directory path, None on failure
    """
    # Load configuration
    if config_file:
        config = MovieOrgConfig(Path(config_file))
    else:
        # Auto-detect configuration file
        config_path = Path(__file__).parent.parent / "configs" / "movie_org_util.yml"
        if config_path.exists():
            config = MovieOrgConfig(config_path)
        else:
            config = MovieOrgConfig()

    # Create organizer and process
    organizer = MovieOrganizer(config)
    return organizer.create_movie_directory_by_detail(movie_details)
