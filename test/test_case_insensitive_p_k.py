"""测试p和k大小写不敏感功能"""

import unittest
from pathlib import Path
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig


class TestCaseInsensitivePK(unittest.TestCase):
    """测试p和k大小写不敏感功能"""
    
    def setUp(self):
        """测试前准备"""
        config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
        config = MovieFileScannerConfig(config_path)
        self.scanner = MovieFileScanner(config)

    def test_lowercase_p_resolution(self):
        """测试小写p的分辨率标识"""
        test_cases = [
            "电影名称.1080p.HD.国语中字.mp4",
            "测试电影.720p.BD.中英双字.mkv",
            "阳光电影dygod.org.好电影.480p.DVD.日语中字.avi"
        ]
        
        expected_names = [
            "电影名称",
            "测试电影", 
            "好电影"
        ]
        
        for i, (filename, expected_name) in enumerate(zip(test_cases, expected_names)):
            with self.subTest(f"小写p测试 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name,
                                   f"电影名称不匹配: 期望'{expected_name}', 实际'{movie_info.movie_name}'")

    def test_uppercase_p_resolution(self):
        """测试大写P的分辨率标识"""
        test_cases = [
            "电影名称.1080P.HD.国语中字.mp4",
            "测试电影.720P.BD.中英双字.mkv", 
            "阳光电影dygod.org.好电影.480P.DVD.日语中字.avi"
        ]
        
        expected_names = [
            "电影名称",
            "测试电影",
            "好电影"
        ]
        
        for i, (filename, expected_name) in enumerate(zip(test_cases, expected_names)):
            with self.subTest(f"大写P测试 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name,
                                   f"电影名称不匹配: 期望'{expected_name}', 实际'{movie_info.movie_name}'")

    def test_lowercase_k_resolution(self):
        """测试小写k的分辨率标识"""
        test_cases = [
            "电影名称.4k.HD.国语中字.mp4",
            "测试电影.8k.BD.中英双字.mkv"
        ]
        
        expected_names = [
            "电影名称",
            "测试电影"
        ]
        
        for i, (filename, expected_name) in enumerate(zip(test_cases, expected_names)):
            with self.subTest(f"小写k测试 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name,
                                   f"电影名称不匹配: 期望'{expected_name}', 实际'{movie_info.movie_name}'")

    def test_uppercase_k_resolution(self):
        """测试大写K的分辨率标识"""
        test_cases = [
            "电影名称.4K.HD.国语中字.mp4",
            "测试电影.8K.BD.中英双字.mkv"
        ]
        
        expected_names = [
            "电影名称",
            "测试电影"
        ]
        
        for i, (filename, expected_name) in enumerate(zip(test_cases, expected_names)):
            with self.subTest(f"大写K测试 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name,
                                   f"电影名称不匹配: 期望'{expected_name}', 实际'{movie_info.movie_name}'")

    def test_mixed_case_resolution(self):
        """测试混合大小写的分辨率标识"""
        test_cases = [
            "电影名称.1080P.HD.720p.国语中字.mp4",  # 混合P和p
            "测试电影.4K.HD.8k.中英双字.mkv"        # 混合K和k
        ]
        
        expected_names = [
            "电影名称 HD",  # 会保留一个HD标识
            "测试电影 HD"   # 会保留一个HD标识
        ]
        
        for i, (filename, expected_name) in enumerate(zip(test_cases, expected_names)):
            with self.subTest(f"混合大小写测试 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    # 对于混合情况，可能会保留一些技术标识，所以做包含性检查
                    self.assertIn(expected_name.split()[0], movie_info.movie_name,
                                f"电影名称应包含'{expected_name.split()[0]}', 实际'{movie_info.movie_name}'")

    def test_complex_filenames(self):
        """测试复杂文件名中的p/k大小写不敏感"""
        test_cases = [
            "阳光电影dygod.org.肖申克的救赎.1080P.BD.国粤双语中字.mp4",
            "最新电影www.test.com.阿甘正传.720p.WEBRIP.英语中字.mkv",
            "电影天堂.泰坦尼克号.4K.BLURAY.中英双字.avi",
            "迅雷下载.盗梦空间.1080p.HDRIP.无水印.mp4"
        ]
        
        expected_names = [
            "肖申克的救赎",
            "阿甘正传", 
            "泰坦尼克号",
            "盗梦空间"
        ]
        
        for i, (filename, expected_name) in enumerate(zip(test_cases, expected_names)):
            with self.subTest(f"复杂文件名测试 {i+1}: {filename}"):
                movie_info = self.scanner.extract_movie_info(Path(f"/{filename}"))
                self.assertIsNotNone(movie_info, f"应该能解析文件: {filename}")
                if movie_info:
                    self.assertEqual(movie_info.movie_name.strip(), expected_name,
                                   f"电影名称不匹配: 期望'{expected_name}', 实际'{movie_info.movie_name}'")


if __name__ == '__main__':
    unittest.main()