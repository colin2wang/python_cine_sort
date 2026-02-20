#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movie sort utility test
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil

from utils.movie_sort_util import do_movie_sort_from_folder


class TestMovieSortUtil(unittest.TestCase):
    
    def setUp(self):
        """Test preparation"""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test movie files
        test_files = [
            "Inception.2010.1080p.BluRay.mp4",
            "The.Matrix.1999.HD.avi", 
            "Interstellar.2014.BD.mkv"
        ]
        
        for filename in test_files:
            (self.test_path / filename).touch()

    def tearDown(self):
        """Test cleanup"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('utils.movie_sort_util.scanner')
    @patch('utils.movie_sort_util.get_movie_search_result_html')
    @patch('utils.movie_sort_util.parse_movie_search_result')
    @patch('utils.movie_sort_util.logger')
    def test_do_movie_sort_from_folder_success(self, mock_logger, mock_parse, mock_get_html, mock_scanner):
        """Test successful movie sorting scenario"""
        # Mock scanner to return test movie info
        mock_movie1 = MagicMock()
        mock_movie1.movie_name = "Inception"
        mock_movie1.year = "2010"
        mock_movie1.file_path = self.test_path / "Inception.2010.1080p.BluRay.mp4"
        
        mock_movie2 = MagicMock()
        mock_movie2.movie_name = "The Matrix"
        mock_movie2.year = "1999"
        mock_movie2.file_path = self.test_path / "The.Matrix.1999.HD.avi"
        
        mock_scanner.scan_directory.return_value = [mock_movie1, mock_movie2]
        
        # Mock HTML response
        mock_html_response = "<html><div class='result'>[电影] Inception</div></html>"
        mock_get_html.return_value = mock_html_response
        
        # Mock parsed movie info
        mock_parsed_info = {
            'title': 'Inception',
            'rating': '9.0',
            'directors': ['Christopher Nolan'],
            'actors': ['Leonardo DiCaprio'],
            'year': '2010',
            'genres': ['Sci-Fi'],
            'original_title': 'Inception',
            'review_count': '1000000',
            'sid': '1234567',
            'error': None
        }
        mock_parse.return_value = mock_parsed_info
        
        # Execute function
        do_movie_sort_from_folder(str(self.test_path))
        
        # Verify scanner was called with correct path
        mock_scanner.scan_directory.assert_called_once_with(self.test_path)
        
        # Verify HTML requests were made
        expected_calls = [
            unittest.mock.call("Inception", "2010"),
            unittest.mock.call("The Matrix", "1999")
        ]
        mock_get_html.assert_has_calls(expected_calls, any_order=False)
        
        # Verify parsing was called
        mock_parse.assert_called_with(mock_html_response)
        
        # Verify logging calls
        mock_logger.info.assert_any_call("✓ Successfully obtained 55 character response")
        mock_logger.info.assert_any_call("✓ Obtained movie information:")
        mock_logger.info.assert_any_call(mock_parsed_info)

    @patch('utils.movie_sort_util.scanner')
    @patch('utils.movie_sort_util.get_movie_search_result_html')
    @patch('utils.movie_sort_util.parse_movie_search_result')
    @patch('utils.movie_sort_util.logger')
    def test_do_movie_sort_from_folder_no_results(self, mock_logger, mock_parse, mock_get_html, mock_scanner):
        """Test scenario where no movies are found"""
        # Mock empty scanner result
        mock_scanner.scan_directory.return_value = []
        
        # Execute function
        do_movie_sort_from_folder(str(self.test_path))
        
        # Verify scanner was called
        mock_scanner.scan_directory.assert_called_once_with(self.test_path)
        
        # Verify no HTML requests were made
        mock_get_html.assert_not_called()
        mock_parse.assert_not_called()
        
        # Verify no info logging occurred for movie processing
        mock_logger.info.assert_not_called()

    @patch('utils.movie_sort_util.scanner')
    @patch('utils.movie_sort_util.get_movie_search_result_html')
    @patch('utils.movie_sort_util.parse_movie_search_result')
    @patch('utils.movie_sort_util.logger')
    def test_do_movie_sort_from_folder_html_request_failure(self, mock_logger, mock_parse, mock_get_html, mock_scanner):
        """Test scenario where HTML request fails"""
        # Mock scanner result
        mock_movie = MagicMock()
        mock_movie.movie_name = "Inception"
        mock_movie.year = "2010"
        mock_scanner.scan_directory.return_value = [mock_movie]
        
        # Mock failed HTML request
        mock_get_html.return_value = None
        
        # Execute function
        do_movie_sort_from_folder(str(self.test_path))
        
        # Verify warning was logged
        mock_logger.warning.assert_called_with("✗ Query failed")
        
        # Verify parsing was still attempted (with None)
        mock_parse.assert_called_with(None)

    @patch('utils.movie_sort_util.scanner')
    @patch('utils.movie_sort_util.get_movie_search_result_html')
    @patch('utils.movie_sort_util.parse_movie_search_result')
    @patch('utils.movie_sort_util.logger')
    def test_do_movie_sort_from_folder_parsing_failure(self, mock_logger, mock_parse, mock_get_html, mock_scanner):
        """Test scenario where parsing returns None or empty result"""
        # Mock scanner result
        mock_movie = MagicMock()
        mock_movie.movie_name = "Inception"
        mock_movie.year = "2010"
        mock_scanner.scan_directory.return_value = [mock_movie]
        
        # Mock successful HTML but failed parsing
        mock_get_html.return_value = "<html>content</html>"
        mock_parse.return_value = None  # Simulate parsing failure
        
        # Execute function
        do_movie_sort_from_folder(str(self.test_path))
        
        # Verify HTML request succeeded
        mock_logger.info.assert_any_call("✓ Successfully obtained 19 character response")
        
        # Verify parsing was attempted
        mock_parse.assert_called_with("<html>content</html>")
        
        # Verify no success logging for movie info (since parsing failed)
        # Check that info logging for "Obtained movie information" didn't occur
        info_calls = [call for call in mock_logger.info.call_args_list 
                     if "Obtained movie information" in str(call)]
        self.assertEqual(len(info_calls), 0)

    @patch('utils.movie_sort_util.scanner')
    @patch('utils.movie_sort_util.get_movie_search_result_html')
    @patch('utils.movie_sort_util.parse_movie_search_result')
    @patch('utils.movie_sort_util.logger')
    def test_do_movie_sort_from_folder_large_html_response(self, mock_logger, mock_parse, mock_get_html, mock_scanner):
        """Test handling of large HTML responses"""
        # Mock scanner result
        mock_movie = MagicMock()
        mock_movie.movie_name = "Long Title Movie"
        mock_movie.year = "2020"
        mock_scanner.scan_directory.return_value = [mock_movie]
        
        # Mock large HTML response (>300 characters)
        large_html = "<html>" + "x" * 500 + "</html>"
        mock_get_html.return_value = large_html
        
        # Mock successful parsing
        mock_parsed_info = {'title': 'Test Movie', 'error': None}
        mock_parse.return_value = mock_parsed_info
        
        # Execute function
        do_movie_sort_from_folder(str(self.test_path))
        
        # Verify debug logging with truncated preview
        mock_logger.debug.assert_called()
        debug_call = mock_logger.debug.call_args[0][0]
        self.assertTrue(debug_call.startswith("Response preview: "))
        self.assertTrue("..." in debug_call)

    @patch('utils.movie_sort_util.scanner')
    @patch('utils.movie_sort_util.get_movie_search_result_html')
    @patch('utils.movie_sort_util.parse_movie_search_result')
    @patch('utils.movie_sort_util.logger')
    def test_do_movie_sort_from_folder_multiple_movies(self, mock_logger, mock_parse, mock_get_html, mock_scanner):
        """Test processing multiple movies"""
        # Mock multiple movies
        movies = []
        for i in range(3):
            mock_movie = MagicMock()
            mock_movie.movie_name = f"Movie {i+1}"
            mock_movie.year = str(2020 + i)
            movies.append(mock_movie)
        
        mock_scanner.scan_directory.return_value = movies
        
        # Mock successful responses
        mock_get_html.return_value = "<html>response</html>"
        mock_parse.return_value = {'title': 'Test Movie', 'error': None}
        
        # Execute function
        do_movie_sort_from_folder(str(self.test_path))
        
        # Verify all movies were processed (3 HTML requests)
        self.assertEqual(mock_get_html.call_count, 3)
        self.assertEqual(mock_parse.call_count, 3)
        
        # Verify sequential processing
        expected_calls = [
            unittest.mock.call(f"Movie {i+1}", str(2020 + i))
            for i in range(3)
        ]
        mock_get_html.assert_has_calls(expected_calls, any_order=False)

    @patch('utils.movie_sort_util.Path')
    @patch('utils.movie_sort_util.MovieFileScannerConfig')
    @patch('utils.movie_sort_util.MovieFileScanner')
    def test_module_import_and_initialization(self, mock_scanner_class, mock_config_class, mock_path_class):
        """Test module-level imports and initialization"""
        # Mock the path resolution
        mock_config_path = MagicMock()
        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_config_path)
        mock_path_class.return_value = mock_path_instance
        mock_path_instance.parent.parent = mock_path_instance
        
        # Mock config and scanner classes
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        # Re-import to test module initialization
        import importlib
        import utils.movie_sort_util
        importlib.reload(utils.movie_sort_util)
        
        # Verify path construction
        mock_path_class.assert_called_with(utils.movie_sort_util.__file__)
        mock_path_instance.__truediv__.assert_called_with("configs")
        
        # Verify config loading
        mock_config_class.assert_called_with(mock_config_path)
        
        # Verify scanner initialization
        mock_scanner_class.assert_called_with(mock_config)


if __name__ == '__main__':
    unittest.main(verbosity=2)