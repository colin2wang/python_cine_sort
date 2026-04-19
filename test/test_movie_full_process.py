#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movie file scanner test
"""

import unittest
from pathlib import Path

from utils import get_default_logger, get_movie_search_result_html, parse_movie_search_result
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig

# Get default logger
logger = get_default_logger()

class TestMovieFileScanner(unittest.TestCase):
    
    def setUp(self):
        """Preparation before testing"""
        # Get configuration file path
        config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
        config = MovieFileScannerConfig(config_path)
        self.scanner = MovieFileScanner(config)

    def tearDown(self):
        """Cleanup after testing"""
        # Clean up temporary files or resources that may have been created during testing
        pass
                    
    def test_full_process_with_folder(self):
        """Test folder scanning functionality"""
        folder_path = Path("I:/我的电影/[待整理]")
        movies = self.scanner.scan_directory(folder_path)
        for movie in movies:
            result_html = get_movie_search_result_html(movie.movie_name, movie.year)

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

    def test_full_process_with_filename(self):
        """Test single filename processing functionality"""
        # Test with sample filenames
        test_filenames = [
            "挽救计划 Project Hail Mary.1080p.HD修正中英双字[最新电影www.5266ys.com].mp4",
            # "Inception.2010.720p.HDTV.AAC.mp4",
            # "Interstellar.2014.4K.UHD.avi",
        ]
        
        for filename in test_filenames:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing filename: {filename}")
            logger.info(f"{'='*60}")
            
            # Create a temporary Path object to simulate a file
            temp_file_path = Path(filename)
            
            # Extract movie information from filename
            movie_info = self.scanner.extract_movie_info(temp_file_path)
            
            if movie_info:
                logger.info(f"✓ Extracted movie info:")
                logger.info(f"  - Movie Name: {movie_info.movie_name}")
                logger.info(f"  - Year: {movie_info.year}")
                logger.info(f"  - Extension: {movie_info.extension}")
                logger.info(f"  - Raw Filename: {movie_info.raw_filename}")
                
                # Search on Douban
                result_html = get_movie_search_result_html(movie_info.movie_name, movie_info.year)
                
                if result_html:
                    logger.info(f"✓ Successfully obtained {len(result_html)} characters from Douban")
                    preview = result_html[:300] + "..." if len(result_html) > 300 else result_html
                    logger.debug(f"Response preview: {preview[:100]}...")
                else:
                    logger.warning("✗ Douban query failed")
                    continue
                
                # Parse search results
                parsed_info = parse_movie_search_result(result_html)
                
                if parsed_info and parsed_info.get('title'):
                    logger.info(f"✓ Parsed Douban movie information:")
                    logger.info(f"  - Title: {parsed_info.get('title', 'N/A')}")
                    logger.info(f"  - Rating: {parsed_info.get('rating', 'N/A')}")
                    logger.info(f"  - Year: {parsed_info.get('year', 'N/A')}")
                    logger.info(f"  - Directors: {', '.join(parsed_info.get('directors', []))}")
                    logger.info(f"  - Actors: {', '.join(parsed_info.get('actors', [])[:3])}")
                    logger.info(f"  - SID: {parsed_info.get('sid', 'N/A')}")
                else:
                    logger.warning("✗ Failed to parse Douban results")
            else:
                logger.error(f"✗ Failed to extract movie info from: {filename}")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)