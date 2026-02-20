from pathlib import Path

from utils import MovieFileScannerConfig, MovieFileScanner, get_movie_search_result_html, get_default_logger, \
    parse_movie_search_result

config_path = Path(__file__).parent.parent / "configs" / "movie_file_util.yml"
config = MovieFileScannerConfig(config_path)
scanner = MovieFileScanner(config)

# Get default logger
logger = get_default_logger()

def do_movie_sort_from_folder(folder_path: str):
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