"""Movie organization utility module

Used to organize movie files into structured directories with metadata files

filename: movie_org_util.py
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

import yaml

from .logging_util import get_default_logger

logger = get_default_logger()


@dataclass
class MovieOrgConfig:
    """Movie organizer configuration class"""
    
    base_folder: str = "I:/我的电影/已整理"
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
            self.base_folder = config.get('base_folder', self.base_folder)
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
        self.logger = get_default_logger()
    
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
            base_path = Path(self.config.base_folder)
            movie_dir = base_path / dir_name
            
            # Create directory (including parent directories)
            movie_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✓ Created directory: {movie_dir}")
            
            # Create metadata files
            if self.config.create_sid_file and sid:
                sid_file = movie_dir / "sid.txt"
                self._write_text_file(sid_file, sid)
                self.logger.info(f"✓ Created SID file: {sid_file}")
            
            if self.config.create_rating_file and rating:
                rating_file = movie_dir / "rating.txt"
                self._write_text_file(rating_file, rating)
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
