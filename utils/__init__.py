# -*- coding: utf-8 -*-
"""
Utility package initialization file
"""

# Logging utilities
from .logging_util import (
    LogConfig,
    setup_logging,
    get_logger,
    setup_default_logging,
    setup_debug_logging,
    setup_error_logging,
    get_default_logger,
    debug,
    info,
    warning,
    error,
    critical,
    LogLevelContext,
    log_exceptions
)

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

# Movie file
from .movie_filename_util import (
    MovieFileInfo,
    MovieFileScannerConfig,
    MovieFileScanner,
    scan_movies_from_directory
)

__all__ = [
    # Logging utilities
    'LogConfig',
    'setup_logging',
    'get_logger',
    'setup_default_logging',
    'setup_debug_logging',
    'setup_error_logging',
    'get_default_logger',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'LogLevelContext',
    'log_exceptions',
    
    # Douban Search
    'get_movie_search_result_html',
    'parse_movie_search_result',

    # Douban Details
    'get_movie_details_html',
    'parse_movie_details_result',
    
    # Movie file scanning utilities
    'MovieFileInfo',
    'MovieFileScannerConfig',
    'MovieFileScanner',
    'scan_movies_from_directory',
]
