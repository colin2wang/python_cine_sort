#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Douban movie details functionality unit test
"""

import os
import sys
import unittest
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.douban_details import get_movie_details_html
from utils.logging_util import setup_default_logging

# Initialize logging
logger = setup_default_logging()


class TestDoubanDetails(unittest.TestCase):
    """Test Douban movie details functionality"""

    def setUp(self):
        """Preparation before testing"""
        self.test_sid = "1292052"  # SID for The Shawshank Redemption

    def tearDown(self):
        """Cleanup after testing"""
        pass

    def test_get_movie_details_success(self):
        """Test successful movie details retrieval"""
        html_content = get_movie_details_html(self.test_sid)
        logger.info(f"HTML content: {html_content}...")



if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)