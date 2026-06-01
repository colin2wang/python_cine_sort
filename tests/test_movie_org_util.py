#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movie organizer test
"""

import shutil
import unittest
from pathlib import Path

import yaml

from utils.logging_config import setup_logger
from utils.movie_org_util import MovieOrganizer, MovieOrgConfig, organize_movie, organize_movie_by_detail

# Get logger
logger = setup_logger(__name__)

# Path to the test configuration file
TEST_CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "test.yml"


class TestMovieOrganizer(unittest.TestCase):

    def setUp(self):
        """Preparation before testing"""
        # Load configuration from config/test.yml
        with open(TEST_CONFIG_FILE, 'r', encoding='utf-8') as f:
            self.test_config = yaml.safe_load(f)

        # Resolve test output directory relative to project root
        test_output_rel = self.test_config.get('test_output_dir', './test-output')
        self.test_root = (Path.cwd() / test_output_rel).resolve()

        # Create a subdirectory for this specific test to avoid conflicts
        self.test_dir_path = self.test_root / self._testMethodName
        if self.test_dir_path.exists():
            shutil.rmtree(self.test_dir_path)
        self.test_dir_path.mkdir(parents=True, exist_ok=True)

        # Build MovieOrgConfig from config/test.yml values
        self.config = MovieOrgConfig()
        self.config.movie_folder = str(self.test_dir_path)
        self.config.directory_format = self.test_config.get('directory_format',
                                                            self.config.directory_format)
        self.config.file_encoding = self.test_config.get('file_encoding',
                                                         self.config.file_encoding)
        self.config.create_rating_file = self.test_config.get('create_rating_file',
                                                              self.config.create_rating_file)
        self.config.create_sid_file = self.test_config.get('create_sid_file',
                                                           self.config.create_sid_file)
        self.organizer = MovieOrganizer(self.config)

    def tearDown(self):
        """Cleanup after testing"""
        if hasattr(self, 'test_root') and self.test_root.exists():
            shutil.rmtree(self.test_root)

    def _create_temp_config(self) -> str:
        """Create a temporary config file pointing to the test directory

        Used for tests that call standalone convenience functions
        (organize_movie / organize_movie_by_detail) which create their own config.

        Returns:
            str: Path to the temporary config file
        """
        config_path = self.test_dir_path / "test_config.yml"
        config_data = {
            'movie_folder': str(self.test_dir_path),
            'directory_format': self.test_config.get('directory_format',
                                                     '{chinese_title}.{english_title}.{year}'),
            'file_encoding': self.test_config.get('file_encoding', 'utf-8'),
            'create_rating_file': self.test_config.get('create_rating_file', True),
            'create_sid_file': self.test_config.get('create_sid_file', True),
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        return str(config_path)
    
    def test_create_movie_directory_with_complete_info(self):
        """Test creating movie directory with complete information"""
        # Sample movie information (like "7号房的礼物")
        movie_info = {
            'title': '7号房的礼物',
            'original_title': 'Gift From Room',
            'year': '2013',
            'sid': '25746891',
            'rating': '8.9'
        }
        
        # Create directory
        result_dir = self.organizer.create_movie_directory(movie_info)
        
        # Verify results
        self.assertIsNotNone(result_dir, "Directory creation should succeed")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        # Check directory name format
        expected_name = "7号房的礼物.Gift.From.Room.2013"
        self.assertEqual(result_dir.name, expected_name, 
                        f"Directory name should be '{expected_name}'")
        
        # Check sid.txt file
        sid_file = result_dir / "25746891.txt"
        self.assertTrue(sid_file.exists(), "sid.txt should exist with SID as filename")
        with open(sid_file, 'r', encoding='utf-8') as f:
            sid_content = f.read().strip()
        self.assertEqual(sid_content, '25746891', "SID content should match")
        
        # Check rating file (filename is the rating value, content is empty)
        rating_file = result_dir / "8.9.txt"
        self.assertTrue(rating_file.exists(), "rating file should exist with rating as filename")
        with open(rating_file, 'r', encoding='utf-8') as f:
            rating_content = f.read()
        self.assertEqual(rating_content, '', "Rating file content should be empty")
        
        logger.info(f"✓ Successfully created directory: {result_dir}")
        logger.info(f"  - SID: {sid_content}")
        logger.info(f"  - Rating: {rating_content}")
    
    def test_create_movie_directory_with_minimal_info(self):
        """Test creating movie directory with minimal information"""
        movie_info = {
            'title': '测试电影',
            'original_title': '',
            'year': '',
            'sid': '',
            'rating': ''
        }
        
        result_dir = self.organizer.create_movie_directory(movie_info)
        
        # Should still create directory even without optional fields
        self.assertIsNotNone(result_dir, "Directory should be created with minimal info")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        logger.info(f"✓ Created directory with minimal info: {result_dir}")
    
    def test_convenience_function(self):
        """Test the convenience function organize_movie"""
        movie_info = {
            'title': '肖申克的救赎',
            'original_title': 'The Shawshank Redemption',
            'year': '1994',
            'sid': '1292052',
            'rating': '9.7'
        }
        
        # Use convenience function with temporary config
        config_file = self._create_temp_config()
        result_dir = organize_movie(movie_info, config_file=config_file)
        
        self.assertIsNotNone(result_dir, "Convenience function should work")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        logger.info(f"✓ Convenience function created: {result_dir}")
    
    def test_invalid_characters_in_title(self):
        """Test handling of invalid characters in movie title"""
        movie_info = {
            'title': '测试:电影/名称<带>特殊*字符?',
            'original_title': 'Test:Movie/Name',
            'year': '2020',
            'sid': '123456',
            'rating': '7.5'
        }
        
        result_dir = self.organizer.create_movie_directory(movie_info)
        
        self.assertIsNotNone(result_dir, "Should handle invalid characters")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        # Verify that invalid characters were replaced
        dir_name = result_dir.name
        self.assertNotIn(':', dir_name, "Colon should be removed")
        self.assertNotIn('/', dir_name, "Slash should be removed")
        self.assertNotIn('<', dir_name, "Less than should be removed")
        self.assertNotIn('>', dir_name, "Greater than should be removed")
        self.assertNotIn('*', dir_name, "Asterisk should be removed")
        self.assertNotIn('?', dir_name, "Question mark should be removed")
        
        logger.info(f"✓ Handled invalid characters correctly: {dir_name}")
    
    def test_missing_title(self):
        """Test behavior when title is missing"""
        movie_info = {
            'title': '',
            'original_title': 'Some Movie',
            'year': '2020',
            'sid': '123456',
            'rating': '7.5'
        }
        
        result_dir = self.organizer.create_movie_directory(movie_info)
        
        # Should return None when title is missing
        self.assertIsNone(result_dir, "Should return None when title is missing")
    
    def test_create_movie_directory_with_douban_details(self):
        """Test creating movie directory with complete Douban details"""
        # Sample movie details (simulating parse_movie_details_result output)
        movie_details = {
            'search_title': '肖申克的救赎',
            'title': '肖申克的救赎',
            'original_title': 'The Shawshank Redemption',
            'year': '1994',
            'sid': '1292052',
            'rating': '9.7',
            'rating_count': 2500000,
            'top250_rank': 1,
            'directors': ['弗兰克·德拉邦特'],
            'actors': ['蒂姆·罗宾斯', '摩根·弗里曼', '鲍勃·冈顿', '威廉姆·赛德勒'],
            'genres': ['剧情', '犯罪'],
            'country': '美国',
            'language': '英语',
            'runtime': 142,
            'imdb_id': 'tt0111161',
            'release_dates': ['1994-09-10(多伦多电影节)', '1994-10-14(美国)'],
            'description': '一场谋杀案使银行家安迪蒙冤入狱，谋杀妻子及其情人的罪名将让他终身监禁。他在监狱中度过了二十年，在狱友瑞德的帮助下，最终成功越狱并重获自由。',
            'short_comments_count': 150000,
            'reviews_count': 8000,
            'awards': [
                {
                    'event': '奥斯卡金像奖',
                    'category': '最佳影片(提名)',
                    'recipient': ''
                }
            ],
            'similar_movies': [
                {'sid': '1291546', 'title': '霸王别姬', 'rating': 9.6},
                {'sid': '1292063', 'title': '美丽人生', 'rating': 9.5}
            ]
        }
        
        # Create directory
        result_dir = self.organizer.create_movie_directory_by_detail(movie_details)
        
        # Verify results
        self.assertIsNotNone(result_dir, "Directory creation should succeed")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        # Check directory name format
        expected_name = "肖申克的救赎.The.Shawshank.Redemption.1994"
        self.assertEqual(result_dir.name, expected_name, 
                        f"Directory name should be '{expected_name}'")
        
        # Check rating file (filename is the rating value, content is empty)
        rating_file = result_dir / "9.7.txt"
        self.assertTrue(rating_file.exists(), "rating file should exist with rating as filename")
        with open(rating_file, 'r', encoding='utf-8') as f:
            rating_content = f.read()
        self.assertEqual(rating_content, '', "Rating file content should be empty")
        
        # Check sid.txt file with detailed information
        sid_file = result_dir / "1292052.txt"
        self.assertTrue(sid_file.exists(), "sid.txt should exist with SID as filename")
        with open(sid_file, 'r', encoding='utf-8') as f:
            sid_content = f.read()
        
        # Verify sid.txt contains key information
        self.assertIn('豆瓣ID: 1292052', sid_content, "SID should be in file")
        self.assertIn('豆瓣评分: 9.7', sid_content, "Rating should be in file")
        self.assertIn('导演: 弗兰克·德拉邦特', sid_content, "Director should be in file")
        self.assertIn('类型: 剧情, 犯罪', sid_content, "Genres should be in file")
        self.assertIn('制片国家/地区: 美国', sid_content, "Country should be in file")
        self.assertIn('语言: 英语', sid_content, "Language should be in file")
        self.assertIn('片长: 142分钟', sid_content, "Runtime should be in file")
        self.assertIn('IMDb: tt0111161', sid_content, "IMDb ID should be in file")
        self.assertIn('剧情简介', sid_content, "Description section should exist")
        self.assertIn('一场谋杀案使银行家安迪蒙冤入狱', sid_content, "Description content should be in file")
        self.assertIn('Top250排名: #1', sid_content, "Top250 rank should be in file")
        self.assertIn('评分人数: 2500000', sid_content, "Rating count should be in file")
        
        logger.info(f"✓ Successfully created directory with details: {result_dir}")
        logger.info(f"  - Rating: {rating_content}")
        logger.info(f"  - SID file content preview:")
        for line in sid_content.split('\n')[:10]:
            logger.info(f"    {line}")
    
    def test_create_movie_directory_with_minimal_details(self):
        """Test creating movie directory with minimal Douban details"""
        movie_details = {
            'title': '测试电影',
            'year': '2020'
        }
        
        result_dir = self.organizer.create_movie_directory_by_detail(movie_details)
        
        # Should still create directory even without optional fields
        self.assertIsNotNone(result_dir, "Directory should be created with minimal info")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        # Check sid.txt exists but has minimal content
        sid_file = result_dir / "sid.txt"
        self.assertTrue(sid_file.exists(), "sid.txt should exist")
        with open(sid_file, 'r', encoding='utf-8') as f:
            sid_content = f.read()
        
        self.assertIn('中文名称: 测试电影', sid_content, "Title should be in file")
        self.assertIn('暂无剧情简介', sid_content, "Should show no description message")
        
        logger.info(f"✓ Created directory with minimal details: {result_dir}")
    
    def test_convenience_function_with_details(self):
        """Test the convenience function organize_movie_by_detail"""
        movie_details = {
            'search_title': '7号房的礼物',
            'title': '7号房的礼物',
            'original_title': 'Gift From Room',
            'year': '2013',
            'sid': '25746891',
            'rating': '8.9',
            'description': '一个充满温情的故事，讲述了父女之间深厚的感情。',
            'directors': ['李焕庆'],
            'genres': ['剧情', '喜剧'],
            'country': '韩国'
        }
        
        # Use convenience function with temporary config
        config_file = self._create_temp_config()
        result_dir = organize_movie_by_detail(movie_details, config_file=config_file)
        
        self.assertIsNotNone(result_dir, "Convenience function should work")
        self.assertTrue(result_dir.exists(), "Directory should exist")
        
        # Verify sid.txt contains description
        sid_file = result_dir / "25746891.txt"
        with open(sid_file, 'r', encoding='utf-8') as f:
            sid_content = f.read()
        
        self.assertIn('一个充满温情的故事', sid_content, "Description should be in file")
        self.assertIn('导演: 李焕庆', sid_content, "Director should be in file")
        self.assertIn('类型: 剧情, 喜剧', sid_content, "Genres should be in file")
        
        logger.info(f"✓ Convenience function created: {result_dir}")
    
    def test_missing_title_in_details(self):
        """Test behavior when title is missing in details"""
        movie_details = {
            'original_title': 'Some Movie',
            'year': '2020',
            'sid': '123456',
            'rating': '7.5'
        }
        
        result_dir = self.organizer.create_movie_directory_by_detail(movie_details)
        
        # Should return None when title is missing
        self.assertIsNone(result_dir, "Should return None when title is missing")
    
    def test_sid_file_format_structure(self):
        """Test the structure and formatting of sid.txt file"""
        movie_details = {
            'search_title': '测试格式化',
            'title': '测试格式化',
            'original_title': 'Test Format',
            'year': '2021',
            'sid': '999999',
            'rating': '8.5',
            'rating_count': 100000,
            'directors': ['导演A', '导演B'],
            'actors': ['演员1', '演员2', '演员3'],
            'genres': ['动作', '科幻'],
            'country': '中国',
            'language': '汉语普通话',
            'runtime': 120,
            'description': '这是一个测试描述。' * 10,  # Long description
            'awards': [
                {'event': '奖项1', 'category': '类别1', 'recipient': '获奖者1'},
                {'event': '奖项2', 'category': '类别2', 'recipient': '获奖者2'}
            ]
        }
        
        result_dir = self.organizer.create_movie_directory_by_detail(movie_details)
        self.assertIsNotNone(result_dir)
        
        sid_file = result_dir / "999999.txt"
        with open(sid_file, 'r', encoding='utf-8') as f:
            sid_content = f.read()
        
        # Check sections exist (code puts directors/actors under "电影基本信息", not a separate "演职人员" section)
        self.assertIn('电影基本信息', sid_content, "Basic info section should exist")
        self.assertIn('详细信息', sid_content, "Details section should exist")
        self.assertIn('剧情简介', sid_content, "Description section should exist")
        
        # Check separators
        self.assertIn('=' * 50, sid_content, "Section separators should exist")
        self.assertIn('-' * 50, sid_content, "Subsection separators should exist")
        
        # Check multiple directors and actors
        self.assertIn('导演A, 导演B', sid_content, "Multiple directors should be listed")
        self.assertIn('演员1, 演员2, 演员3', sid_content, "Multiple actors should be listed")
        
        # Check awards
        self.assertIn('获奖情况: 共2条记录', sid_content, "Awards count should be shown")
        
        logger.info(f"✓ SID file format verified: {result_dir}")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
