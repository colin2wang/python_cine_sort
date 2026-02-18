#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Douban movie query functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result
from utils.logging_util import setup_default_logging

# Initialize logging
logger = setup_default_logging()

def test_douban_query():
    """Test Douban movie query functionality"""
    logger.info("Testing Douban movie query...")
    
    # Test cases
    test_cases = [
        ("肖申克的救赎", "1994"),
        ("阿甘正传", "1994"),
        ("泰坦尼克号", "1997")
    ]
    
    for name, year in test_cases:
        logger.info(f"\nQuerying movie: {name} ({year})")
        result_html = get_movie_search_result_html(name, year)

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


if __name__ == "__main__":
    test_douban_query()