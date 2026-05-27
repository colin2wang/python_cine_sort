from pathlib import Path

from utils.logging_config import setup_logger
from utils.movie_file_util import MovieFileScannerConfig, MovieFileScanner
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result

config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
config = MovieFileScannerConfig(config_path)
scanner = MovieFileScanner(config)

# Get logger
logger = setup_logger(__name__)

def do_movie_sort_from_folder(folder_path: str):
    """
    Perform movie sorting from a folder by scanning files and fetching Douban information
    
    Args:
        folder_path (str): Path to the folder containing movie files
        
    Returns:
        None: This function does not return any value. It processes movies and logs information.
            For each movie file found:
            - Scans and extracts movie name and year from filename
            - Searches Douban for movie information
            - Parses and logs the search results
            - Logs detailed movie information if successfully retrieved
    """
    movies = scanner.scan_directory(Path(folder_path))
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