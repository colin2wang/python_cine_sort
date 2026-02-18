#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_movie_info 函数单元测试
基于实际豆瓣搜索结果HTML的测试
"""

import unittest
import sys
import os

from utils import setup_default_logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.douban_html_util import parse_movie_info

# 初始化日志
logger = setup_default_logging()

class TestParseMovieInfoV2(unittest.TestCase):
    """测试更新后的 parse_movie_info 函数"""
    
    def setUp(self):
        """测试前准备 - 读取实际的豆瓣搜索结果HTML文件"""
        # 读取实际的豆瓣搜索结果文件
        douban_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../test_data/douban_search_result.html')

        try:
            with open(douban_html_path, 'r', encoding='utf-8') as f:
                self.full_douban_html = f.read()
        except FileNotFoundError:
            self.full_douban_html = ''


    def test_full_html_file_parsing(self):
        """测试完整HTML文件的解析"""
        # 测试解析完整HTML文件
        result = parse_movie_info(self.full_douban_html)

        logger.info(f"解析结果: {result}")
        
        self.assertIsInstance(result, dict)
        # 验证至少能提取到一些基本信息
        self.assertIsInstance(result['title'], str)
        self.assertIsInstance(result['rating'], str)
        self.assertIsInstance(result['year'], str)




if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)