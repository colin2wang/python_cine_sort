#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_movie_info function unit test
Based on actual Douban search result HTML testing
"""

import unittest
import sys
import os

from utils import setup_default_logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.douban_search import parse_movie_search_result

# Initialize logging
logger = setup_default_logging()

class TestParseMovieInfoV2(unittest.TestCase):
    """Test updated parse_movie_info function"""
    
    def setUp(self):
        """Preparation before testing - Read actual Douban search result HTML file"""
        # Read actual Douban search result file
        douban_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../test_data/douban_search_result.html')

        try:
            with open(douban_html_path, 'r', encoding='utf-8') as f:
                self.full_douban_html = f.read()
        except FileNotFoundError:
            self.full_douban_html = ''


    def test_full_html_file_parsing(self):
        """Test parsing of complete HTML file"""
        # Test parsing complete HTML file
        result = parse_movie_search_result(self.full_douban_html)

        logger.info(f"Parsing result: {result}")
        
        self.assertIsInstance(result, dict)
        # Verify that at least some basic information can be extracted
        self.assertIsInstance(result['title'], str)
        self.assertIsInstance(result['rating'], str)
        self.assertIsInstance(result['year'], str)




if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)