#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movie file scanner test
"""

import unittest
from pathlib import Path

from utils import get_default_logger
from utils.movie_filename_util import MovieFileScanner, MovieFileScannerConfig

# Get default logger
logger = get_default_logger()

class TestMovieFileScanner(unittest.TestCase):
    
    def setUp(self):
        """Preparation before testing"""
        # Get configuration file path
        config_path = Path(__file__).parent.parent / "configs" / "movie_filename_util.yml"
        config = MovieFileScannerConfig(config_path)
        self.scanner = MovieFileScanner(config)

    def tearDown(self):
        """Cleanup after testing"""
        # 清理测试过程中可能创建的临时文件或资源
        pass
    
    def test_extract_year(self):
        """Test year extraction functionality"""
        # Test filename with year
        filename_with_year = "阳光电影dygod.org.睡觉的笨蛋.2025.BD.1080P.日语中字.mkv"
        # Extract year directly from original filename
        year = self.scanner._extract_year(filename_with_year)
        self.assertEqual(year, "2025")
        
        # Test filename without year
        filename_without_year = "[Haruhana] Chainsaw Man - Reze Arc [WebRip].mkv"
        year = self.scanner._extract_year(filename_without_year)
        self.assertIsNone(year)
    
    def test_clean_filename(self):
        """Test filename cleaning functionality"""
        # Test cleaning complex filename
        filename = "[Haruhana] Chainsaw Man - Reze Arc [WebRip][HEVC-10bit 1080p][CHS_JPN]"
        movie_name = self.scanner._process_movie_name(filename)
        self.assertEqual("Chainsaw Man Reze Arc", movie_name)

        # Test cleaning Chinese filename
        chinese_filename = "猪猪侠.一只老猪的逆袭.1080p.HD国语中字无水印[最新电影www.5266ys.com]"
        movie_name = self.scanner._process_movie_name(chinese_filename)
        self.assertEqual("猪猪侠 一只老猪的逆袭", movie_name)

        # Test filename with year
        filename_with_year = "阳光电影dygod.org.睡觉的笨蛋.2025.BD.1080P.日语中字.mkv"
        movie_name = self.scanner._process_movie_name(filename_with_year)
        # Expected result should be cleaned name, may still contain year information
        self.assertIn("睡觉的笨蛋", movie_name)
    

    def test_edge_cases(self):
        """Test edge cases"""
        edge_cases = [
            # Minimal filename
            ("电影.2024.mkv", "电影", "2024"),
            # Filename without year
            ("纯电影名称.mp4", "纯电影名称", None),
            # Multiple year numbers
            ("阳光电影dygod.org.测试电影.2024.HD.1080P.mkv", "测试电影", "2024"),
            # Special characters
            ("电影-名称.2024.HD.mp4", "电影 名称", "2024"),
            # Movie name containing numbers
            ("阳光电影dygod.org.我的1919.2020.BD.1080P.国英双语双字.mkv", "我的1919 国英双语双字", "2020")
        ]
        
        for filename, expected_name, expected_year in edge_cases:
            with self.subTest(f"Edge case test: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"Should be able to parse file: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name)
                    self.assertEqual(movie_info.year, expected_year)


    def test_with_folder(self):
        """Test folder scanning functionality"""
        folder_path = Path("I:/我的电影")
        movies = self.scanner.scan_directory(folder_path)
        for movie in movies:
            logger.info(f"movie: {movie}")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)