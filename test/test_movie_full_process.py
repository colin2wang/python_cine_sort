#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movie file scanner test
"""

import unittest
from pathlib import Path

from utils import get_default_logger, get_movie_search_result_html, parse_movie_search_result
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig

# Get default logger
logger = get_default_logger()

class TestMovieFileScanner(unittest.TestCase):
    
    def setUp(self):
        """Preparation before testing"""
        # Get configuration file path
        config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
        config = MovieFileScannerConfig(config_path)
        self.scanner = MovieFileScanner(config)

    def tearDown(self):
        """Cleanup after testing"""
        # 清理测试过程中可能创建的临时文件或资源
        pass
                    
    def test_full_process_with_folder(self):
        """Test folder scanning functionality"""
        folder_path = Path("I:/我的电影")
        movies = self.scanner.scan_directory(folder_path)
        for movie in movies:
            result_html = get_movie_search_result_html(movie.movie_name, movie.year)

            if result_html:
                logger.info(f"✓ Successfully obtained {len(result_html)} character response")
                # Show first 300 characters as preview
                preview = result_html[:300] + "..." if len(result_html) > 300 else result_html
                logger.debug(f"Response preview: {preview[:100]}...")
            else:
                logger.warning("✗ Query failed")

            movie_info = parse_movie_search_result(result_html)

            if movie_info:
                logger.info(f"✓ Obtained movie information:")
                logger.info(movie_info)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)