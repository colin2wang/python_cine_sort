"""Complete movie processing workflow with folder organization

This script integrates all movie utilities to:
1. Scan movie files from directory
2. Search Douban for movie information
3. Get detailed movie information from Douban
4. Organize movies into structured directories with metadata

Usage:
    python process_with_folder.py
    
Note: All configuration is read from config/movie_org_util.yml
"""

from pathlib import Path
from typing import List, Dict, Optional

from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result
from utils.douban_details import get_movie_details_html, parse_movie_details_result
from utils.movie_org_util import organize_movie_by_detail, MovieOrgConfig
from utils.logging_config import setup_logger

logger = setup_logger(__name__)


class MovieProcessor:
    """Complete movie processing workflow manager"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize movie processor

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.logger = setup_logger(__name__)

        # Initialize scanner
        scanner_config_file = self.config_dir / "movie_file_util.yml"
        if scanner_config_file.exists():
            scanner_config = MovieFileScannerConfig(scanner_config_file)
            self.scanner = MovieFileScanner(scanner_config)
            self.logger.info(f"✓ Movie scanner initialized with config: {scanner_config_file}")
        else:
            raise FileNotFoundError(f"Scanner config not found: {scanner_config_file}")

        # Initialize organizer
        org_config_file = self.config_dir / "movie_org_util.yml"
        if org_config_file.exists():
            org_config = MovieOrgConfig(org_config_file)
            self.organizer_config = org_config
            self.logger.info(f"✓ Movie organizer initialized with config: {org_config_file}")
        else:
            raise FileNotFoundError(f"Organizer config not found: {org_config_file}")

        # Statistics
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

    def process_directory(self, input_dir: Path, recursive: bool = True) -> List[Dict]:
        """Process all movie files in directory

        Args:
            input_dir: Input directory containing movie files
            recursive: Whether to scan subdirectories recursively

        Returns:
            List of processing results
        """
        if not input_dir.exists():
            self.logger.error(f"✗ Input directory does not exist: {input_dir}")
            return []

        if not input_dir.is_dir():
            self.logger.error(f"✗ Input path is not a directory: {input_dir}")
            return []

        self.logger.info("=" * 60)
        self.logger.info("Starting movie processing workflow")
        self.logger.info(f"Input directory: {input_dir}")
        self.logger.info(f"Recursive scan: {recursive}")
        self.logger.info("=" * 60)

        # Step 1: Scan movie files
        self.logger.info("\n[Step 1/3] Scanning movie files...")
        movie_files = self.scanner.scan_directory(input_dir, recursive)
        self.stats['total_files'] = len(movie_files)

        if not movie_files:
            self.logger.warning("No movie files found in directory")
            return []

        self.logger.info(f"Found {len(movie_files)} movie files\n")

        # Step 2-4: Process each movie
        results = []
        for idx, movie_file in enumerate(movie_files, 1):
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"[Processing {idx}/{len(movie_files)}] {movie_file.raw_filename}")
            self.logger.info(f"{'=' * 60}")

            result = self.process_single_movie(movie_file)
            results.append(result)

            # Update statistics
            self.stats['processed'] += 1
            if result.get('success'):
                self.stats['success'] += 1
            elif result.get('skipped'):
                self.stats['skipped'] += 1
            else:
                self.stats['failed'] += 1

        # Print summary
        self.print_summary()

        return results

    def process_single_movie(self, movie_file) -> Dict:
        """Process a single movie file through complete workflow

        Args:
            movie_file: MovieFileInfo object from scanner

        Returns:
            Dictionary containing processing result
        """
        result = {
            'filename': movie_file.raw_filename,
            'movie_name': movie_file.movie_name,
            'year': movie_file.year,
            'success': False,
            'skipped': False,
            'directory': None,
            'error': None
        }

        try:
            # Step 2: Search Douban for movie
            self.logger.info(f"\n[Step 2/3] Searching Douban for: {movie_file.movie_name} ({movie_file.year or 'N/A'})")
            search_html = get_movie_search_result_html(movie_file.movie_name, movie_file.year or '')

            if not search_html:
                self.logger.error(f"✗ Failed to get search results from Douban")
                result['error'] = "Failed to get search results"
                return result

            # Parse search results
            search_info = parse_movie_search_result(search_html)

            if not search_info.get('sid'):
                self.logger.error(f"✗ Could not find movie SID from search results")
                result['error'] = "Movie SID not found"
                return result

            sid = search_info['sid']
            self.logger.info(f"✓ Found movie SID: {sid}")
            self.logger.info(f"  Title: {search_info.get('title', 'N/A')}")
            self.logger.info(f"  Rating: {search_info.get('rating', 'N/A')}")

            # Step 3: Get detailed movie information
            self.logger.info(f"\n[Step 3/3] Getting detailed information from Douban (SID: {sid})")
            details_html = get_movie_details_html(sid)

            if not details_html:
                self.logger.error(f"✗ Failed to get movie details from Douban")
                result['error'] = "Failed to get movie details"
                return result

            # Parse movie details
            movie_details = parse_movie_details_result(details_html)

            # Add search title to details
            movie_details['search_title'] = search_info['title']

            if not movie_details:
                self.logger.error(f"✗ Failed to parse movie details")
                result['error'] = "Failed to parse movie details"
                return result

            self.logger.info(f"✓ Successfully parsed movie details:")
            self.logger.info(f"  Chinese Title: {movie_details.get('title', 'N/A')}")
            self.logger.info(f"  Original Title: {movie_details.get('original_title', 'N/A')}")
            self.logger.info(f"  Year: {movie_details.get('year', 'N/A')}")
            self.logger.info(f"  Rating: {movie_details.get('rating', 'N/A')}")
            self.logger.info(f"  Directors: {', '.join(movie_details.get('directors', [])[:3])}")

            # Ensure SID is set in details
            if 'sid' not in movie_details:
                movie_details['sid'] = sid

            # Step 4: Create organized directory structure
            self.logger.info(f"\n[Step 4/4] Creating organized directory structure")
            movie_dir = organize_movie_by_detail(
                movie_details,
                config_file=str(self.config_dir / "movie_org_util.yml")
            )

            if movie_dir:
                self.logger.info(f"✓ Successfully created directory: {movie_dir}")
                result['success'] = True
                result['directory'] = str(movie_dir)
            else:
                self.logger.error(f"✗ Failed to create directory")
                result['error'] = "Failed to create directory"

        except Exception as e:
            self.logger.error(f"✗ Error processing movie: {e}", exc_info=True)
            result['error'] = str(e)

        return result

    def print_summary(self):
        """Print processing summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total files scanned:    {self.stats['total_files']}")
        self.logger.info(f"Processed:              {self.stats['processed']}")
        self.logger.info(f"Successful:             {self.stats['success']}")
        self.logger.info(f"Failed:                 {self.stats['failed']}")
        self.logger.info(f"Skipped:                {self.stats['skipped']}")
        self.logger.info("=" * 60)

        if self.stats['processed'] > 0:
            success_rate = (self.stats['success'] / self.stats['processed']) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info("=" * 60)


def main():
    """Main entry point - no arguments required, all from config"""
    try:
        # Load configuration
        processor = MovieProcessor()
        
        # Get movie directory from configuration (both input and output)
        movie_dir = Path(processor.organizer_config.movie_folder).resolve()
        
        # Validate movie directory
        if not movie_dir.exists():
            print(f"Error: Movie directory does not exist: {movie_dir}")
            print(f"Please check 'movie_folder' in config file: {processor.config_dir / 'movie_org_util.yml'}")
            return 1

        if not movie_dir.is_dir():
            print(f"Error: Movie path is not a directory: {movie_dir}")
            return 1
        
        # Log directory
        print(f"Movie directory (from config): {movie_dir}")
        
        results = processor.process_directory(movie_dir, recursive=True)

        # Return exit code based on results
        if not results:
            return 1

        failed_count = sum(1 for r in results if not r.get('success'))
        return 1 if failed_count > 0 else 0

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
