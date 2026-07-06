# -*- coding: utf-8 -*-
"""
Utility package initialization file
"""

# Logging utilities
from .logging_config import setup_logger

# Douban Search
from .douban_search import (
    get_movie_search_result_html,
    parse_movie_search_result
)

# Douban Details
from .douban_details import (
    get_movie_details_html,
    parse_movie_details_result
)

# Douban Poster
from .douban_poster import (
    get_posters_page_html,
    parse_posters_result,
    download_poster,
    get_movie_poster,
    get_all_movie_posters,
    download_official_posters
)

# Movie file
from .movie_file_util import (
    MovieFileInfo,
    MovieFileScannerConfig,
    MovieFileScanner,
    scan_movies_from_directory
)

# Movie organizer
from .movie_org_util import (
    MovieOrgConfig,
    MovieOrganizer,
    organize_movie,
    organize_movie_by_detail
)

# Database manager
from .db_manager import MovieDB

# IMDB rating
from .imdb_rating import get_imdb_rating

__all__ = [
    # Logging utilities
    'setup_logger',
    
    # Douban Search
    'get_movie_search_result_html',
    'parse_movie_search_result',

    # Douban Details
    'get_movie_details_html',
    'parse_movie_details_result',
    
    # Douban Poster
    'get_posters_page_html',
    'parse_posters_result',
    'download_poster',
    'get_movie_poster',
    'get_all_movie_posters',
    'download_official_posters',
    
    # Movie file scanning utilities
    'MovieFileInfo',
    'MovieFileScannerConfig',
    'MovieFileScanner',
    'scan_movies_from_directory',
    
    # Movie organizer utilities
    'MovieOrgConfig',
    'MovieOrganizer',
    'organize_movie',
    'organize_movie_by_detail',
    
    # Database manager
    'MovieDB',

    # IMDB rating
    'get_imdb_rating',
]
