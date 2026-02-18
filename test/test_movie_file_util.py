#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电影文件扫描器测试
"""

import unittest
from pathlib import Path

from utils import get_default_logger
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig

# 获取默认日志记录器
logger = get_default_logger()

class TestMovieFileScanner(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        # 获取配置文件路径
        config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
        config = MovieFileScannerConfig(config_path)
        self.scanner = MovieFileScanner(config)

    def tearDown(self):
        """测试后清理"""
    
    def test_extract_year(self):
        """测试年份提取功能"""
        # 测试包含年份的文件名
        filename_with_year = "阳光电影dygod.org.睡觉的笨蛋.2025.BD.1080P.日语中字.mkv"
        # 先清理文件名
        cleaned_name = self.scanner._cleanup_filename(filename_with_year)
        year = self.scanner._extract_year_from_cleaned(cleaned_name)
        self.assertEqual(year, "2025")
        
        # 测试不包含年份的文件名
        filename_without_year = "[Haruhana] Chainsaw Man - Reze Arc [WebRip].mkv"
        cleaned_name = self.scanner._cleanup_filename(filename_without_year)
        year = self.scanner._extract_year_from_cleaned(cleaned_name)
        self.assertIsNone(year)
    
    def test_clean_filename(self):
        """测试文件名清理功能"""
        # 测试清理复杂文件名
        filename = "[Haruhana] Chainsaw Man - Reze Arc [WebRip][HEVC-10bit 1080p][CHS_JPN]"
        cleaned_name = self.scanner._cleanup_filename(filename)
        # 从清理后的名称中提取电影名
        movie_name = self.scanner._extract_movie_name_from_cleaned(cleaned_name)
        self.assertEqual("Chainsaw Man Reze Arc", movie_name)

        # 测试清理中文文件名
        chinese_filename = "猪猪侠.一只老猪的逆袭.1080p.HD国语中字无水印[最新电影www.5266ys.com]"
        cleaned_name = self.scanner._cleanup_filename(chinese_filename)
        movie_name = self.scanner._extract_movie_name_from_cleaned(cleaned_name)
        self.assertEqual("猪猪侠 一只老猪的逆袭", movie_name)

        # 测试包含年份的文件名
        filename_with_year = "阳光电影dygod.org.睡觉的笨蛋.2025.BD.1080P.日语中字.mkv"
        cleaned_name = self.scanner._cleanup_filename(filename_with_year)
        movie_name = self.scanner._extract_movie_name_from_cleaned(cleaned_name)
        # 期望结果应该是清理后的名称，可能还包含年份信息
        self.assertIn("睡觉的笨蛋", movie_name)
    
    def test_config_loading(self):
        """测试配置加载功能"""
        # 测试配置文件加载
        config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
        config = MovieFileScannerConfig(config_path)
        self.assertIn('.mkv', config.extensions)
        self.assertIn('.mp4', config.extensions)
        self.assertGreater(len(config.cleanup_rules), 0)
        self.assertGreater(len(config.year_patterns), 0)

        
        # 测试自定义配置
        custom_config = MovieFileScannerConfig(config_path)
        custom_config.extensions = ['.avi', '.mov']
        custom_config.cleanup_rules.append(r'test_pattern')
        self.assertEqual(custom_config.extensions, ['.avi', '.mov'])
        self.assertIn(r'test_pattern', custom_config.cleanup_rules)

    def test_problematic_cases(self):
        """测试有问题的文件名案例"""
        # 测试年份误识别问题
        problematic_files = [
            # 年份在标题中的情况
            "阳光电影dygod.org.唐探1900.2025.BD.1080P.国语中字.mkv",
            # 包含技术信息的情况
            "阳光电影dygod.org.好东西.2024.HD.1080P.国语中英双字.mkv",
            # 包含网站标识的情况
            "阳光电影dygod.org.九龙城寨之围城.2024.BD.1080P.国粤双语中字.mkv",
            # 复杂命名的情况
            "l浪d球2：z次m险.2024.HD1080p.国语中字.mp4",
            # 带括号的情况
            "z近，妹m的y子y点g.电影版.2014.BD1080p.中文字幕.mp4",
            # 菲律宾语电影测试案例
            "Scorpio.Nights.3.2022.HD1080P.X264.AAC.Filipino.CHS-ENG.BDYS.mp4",
            "Ang.Babaeng.Nawawala.sa.Sarili.2022.HD1080P.X264.AAC.Tagalog.CHS-ENG.BDYS.mp4",
            "Top.1.2024.HD1080P.X264.AAC.Tagalog.CHS-ENG.YJYS.mp4",
            "Sitio.Diablo.2022.HD1080P.X264.AAC.Filipino.CHS-ENG.BDYS.mp4",
            "Lampas.Langit.2022.HD1080P.X264.AAC.Filipino.CHS-ENG.BDYS.mp4"
        ]
        
        expected_results = [
            {"name": "唐探1900 1080P", "year": None},  # 年份在清理阶段被移除
            {"name": "好东西 1080P", "year": None},
            {"name": "九龙城寨之围城 1080P", "year": None},
            {"name": "l浪d球2：z次m险", "year": None},
            {"name": "z近，妹m的y子y点g 电影版 中文字幕", "year": None},
            {"name": "Scorpio Nights 3 1080P X264 YS", "year": None},
            {"name": "Ang Babaeng Nawawala sa Sarili 1080P X264 YS", "year": None},
            {"name": "Top 1 1080P X264", "year": None},
            {"name": "Sitio Diablo 1080P X264 YS", "year": None},
            {"name": "Lampas Langit 1080P X264 YS", "year": None}
        ]
        
        for i, (filename, expected) in enumerate(zip(problematic_files, expected_results)):
            with self.subTest(f"测试案例 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected["name"], 
                                   f"电影名称不匹配: 期望'{expected['name']}', 实际'{movie_info.movie_name}'")
                    self.assertEqual(movie_info.year, expected["year"], 
                                   f"年份不匹配: 期望'{expected['year']}', 实际'{movie_info.year}'")
                    
                    logger.info(f"✓ 案例{i+1}通过: {filename}")
                    logger.info(f"  解析结果: 名称='{movie_info.movie_name}', 年份={movie_info.year}")
    
    def test_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            # 极简文件名
            ("电影.2024.mkv", "电影", "2024"),
            # 无年份文件名
            ("纯电影名称.mp4", "纯电影名称", None),
            # 多个年份数字
            ("阳光电影dygod.org.测试电影.2024.HD.1080P.2025版.mkv", "测试电影", "2024"),
            # 特殊字符
            ("电影-名称_2024.HD.mp4", "电影 名称", "2024")
        ]
        
        for filename, expected_name, expected_year in edge_cases:
            with self.subTest(f"边界测试: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name)
                    self.assertEqual(movie_info.year, expected_year)
                    
    def test_with_folder(self):
        """测试文件夹扫描功能"""
        folder_path = Path("I:/我的电影")
        movies = self.scanner.scan_directory(folder_path)
        for movie in movies:
            logger.info(f"movie: {movie}")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)