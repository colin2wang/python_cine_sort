#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movie organizer test
"""

import unittest
from pathlib import Path

from utils import get_default_logger, organize_movie
from utils.movie_org_util import MovieOrganizer, MovieOrgConfig

# Get default logger
logger = get_default_logger()


class TestMovieOrganizer(unittest.TestCase):
    
    def setUp(self):
        """Preparation before testing"""
        # Get configuration file path
        config_path = Path(__file__).parent.parent / "configs" / "movie_org_util.yml"
        self.config = MovieOrgConfig(config_path)
        self.organizer = MovieOrganizer(self.config)
    
    def tearDown(self):
        """Cleanup after testing"""
        # Clean up temporary files or resources that may have been created during testing
        pass
    
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
        sid_file = result_dir / "sid.txt"
        self.assertTrue(sid_file.exists(), "sid.txt should exist")
        with open(sid_file, 'r', encoding='utf-8') as f:
            sid_content = f.read().strip()
        self.assertEqual(sid_content, '25746891', "SID content should match")
        
        # Check rating.txt file
        rating_file = result_dir / "rating.txt"
        self.assertTrue(rating_file.exists(), "rating.txt should exist")
        with open(rating_file, 'r', encoding='utf-8') as f:
            rating_content = f.read().strip()
        self.assertEqual(rating_content, '8.9', "Rating content should match")
        
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
        
        # Use convenience function
        result_dir = organize_movie(movie_info)
        
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


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
