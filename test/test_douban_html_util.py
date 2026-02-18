#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试豆瓣电影查询功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.douban_html_util import get_movie_search_result_html, parse_movie_info
from utils.logging_util import setup_default_logging

# 初始化日志
logger = setup_default_logging()

def test_douban_query():
    """测试豆瓣电影查询功能"""
    logger.info("测试豆瓣电影查询...")
    
    # 测试用例
    test_cases = [
        ("肖申克的救赎", "1994"),
        ("阿甘正传", "1994"),
        ("泰坦尼克号", "1997")
    ]
    
    for name, year in test_cases:
        logger.info(f"\n查询电影: {name} ({year})")
        result_html = get_movie_search_result_html(name, year)

        if result_html:
            logger.info(f"✓ 成功获取到 {len(result_html)} 字符的响应")
            # 显示前300个字符作为预览
            preview = result_html[:300] + "..." if len(result_html) > 300 else result_html
            logger.debug(f"响应预览: {preview[:100]}...")
        else:
            logger.warning("✗ 查询失败")

        movie_info = parse_movie_info(result_html)

        if movie_info:
            logger.info(f"✓ 获取到电影信息:")
            logger.info(movie_info)


if __name__ == "__main__":
    test_douban_query()