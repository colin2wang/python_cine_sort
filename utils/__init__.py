# -*- coding: utf-8 -*-
"""
工具包初始化文件
"""

# 导出主要模块
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

# 导出豆瓣相关功能
from .douban_html_util import (
    get_movie_search_result_html,
    parse_movie_info
)

# 导出电影文件扫描功能
from .movie_file_util import (
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
    
    # Douban utilities
    'get_movie_search_result_html',
    'parse_movie_info',
    
    # Movie file scanning utilities
    'MovieFileInfo',
    'MovieFileScannerConfig',
    'MovieFileScanner',
    'scan_movies_from_directory',
]
