"""Process a single movie by Douban SID

This script takes a Douban movie SID (subject ID), fetches its details,
and creates the organized directory structure under the configured movie_folder.

Usage:
    python process_with_id.py <sid>

Example:
    python process_with_id.py 34884712

Note: All directory configuration is read from config/movie_org_util.yml
"""

import sys
from pathlib import Path
from typing import Optional

from utils.douban_details import get_movie_details_html, parse_movie_details_result
from utils.douban_poster import download_official_posters
from utils.movie_org_util import organize_movie_by_detail, MovieOrgConfig
from utils.db_manager import MovieDB
from utils.imdb_rating import get_imdb_rating
from utils.logging_config import setup_logger

logger = setup_logger(__name__)


def _create_imdb_rating_file(movie_details: dict, movie_dir: str) -> None:
    """Fetch IMDB rating and create IMDB X.X.txt file if rating exists."""
    imdb_id = movie_details.get('imdb_id', '')
    if not imdb_id:
        return

    rating = get_imdb_rating(imdb_id)
    if rating is not None:
        rating_file = Path(movie_dir) / f"IMDB {rating}.txt"
        rating_file.write_text("", encoding='utf-8')
        logger.info(f"✓ Created IMDB rating file: {rating_file.name}")


def process_by_sid(sid: str) -> int:
    """Fetch Douban details for a SID and create organized directory.

    Always fetches fresh data from Douban. Database is write-only.

    Args:
        sid: Douban movie subject ID (e.g. "34884712")

    Returns:
        0 on success, 1 on failure
    """
    # Resolve config path
    config_dir = Path(__file__).parent / "config"
    org_config_file = config_dir / "movie_org_util.yml"

    if not org_config_file.exists():
        print(f"Error: Config file not found: {org_config_file}")
        return 1

    # Load organizer config
    org_config = MovieOrgConfig(org_config_file)
    movie_folder = Path(org_config.movie_folder).resolve()
    print(f"Movie folder (from config): {movie_folder}")

    # Step 1: Fetch Douban details
    logger.info(f"Fetching Douban details for SID: {sid}")
    details_html = get_movie_details_html(sid)

    if not details_html:
        logger.error("✗ Failed to get movie details from Douban")
        return 1

    # Parse movie details
    movie_details = parse_movie_details_result(details_html)

    if not movie_details:
        logger.error("✗ Failed to parse movie details")
        return 1

    if 'sid' not in movie_details:
        movie_details['sid'] = sid

    logger.info("✓ Successfully parsed movie details:")
    logger.info(f"  Chinese Title: {movie_details.get('title', 'N/A')}")
    logger.info(f"  Original Title: {movie_details.get('original_title', 'N/A')}")
    logger.info(f"  Year: {movie_details.get('year', 'N/A')}")
    logger.info(f"  Rating: {movie_details.get('rating', 'N/A')}")
    logger.info(f"  Directors: {', '.join(movie_details.get('directors', [])[:3])}")

    # Step 2: Create organized directory structure
    logger.info("Creating organized directory structure...")
    movie_dir = organize_movie_by_detail(
        movie_details,
        config_file=str(org_config_file)
    )

    if not movie_dir:
        logger.error("✗ Failed to create directory")
        return 1

    print(f"✓ Successfully created directory: {movie_dir}")

    # Create IMDB rating file (alongside other text files)
    _create_imdb_rating_file(movie_details, movie_dir)

    # Step 3: Download official posters
    logger.info("Downloading official posters...")
    poster_dir = Path(movie_dir)
    downloaded_posters, poster_metadata = download_official_posters(
        sid=sid,
        save_dir=str(poster_dir),
        title_keyword="正式海报"
    )

    if downloaded_posters:
        logger.info(f"✓ Downloaded {len(downloaded_posters)} posters")
        for poster_path in downloaded_posters:
            logger.info(f"  - {Path(poster_path).name}")
    else:
        logger.warning("⚠ No posters downloaded")

    # Step 4: Save to database
    logger.info("Saving to database...")
    try:
        db = MovieDB()
        movie_id = db.save_movie(movie_details, directory_path=str(movie_dir))
        logger.info(f"✓ Saved movie to database (ID: {movie_id})")

        if poster_metadata:
            db.save_posters(movie_id, poster_metadata)
            logger.info(f"✓ Saved {len(poster_metadata)} poster records to database")
    except Exception as e:
        logger.error(f"⚠ Failed to save to database: {e}")

    return 0


def print_usage():
    """Print usage information."""
    print(__doc__)
    print("Available commands:")
    print("  <sid>           Douban movie subject ID to process")
    print()
    print("Examples:")
    print("  python process_with_id.py 34884712")


def read_clipboard() -> Optional[str]:
    """Read text from system clipboard.

    Returns:
        Clipboard text stripped of whitespace, or None if unavailable/empty.
    """
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        value = root.clipboard_get()
        root.destroy()
        return value.strip()
    except Exception:
        return None


def get_sid_from_args_or_input() -> Optional[str]:
    """Get SID from command-line argument, clipboard, or prompt for console input.

    Priority:
    1. Command-line argument
    2. Clipboard content (if all digits)
    3. Console prompt

    Returns:
        SID string, or None if user exits.
    """
    # 1. Command-line argument
    if len(sys.argv) >= 2 and sys.argv[1] not in ('-h', '--help'):
        return sys.argv[1].strip()

    # 2. Clipboard (if all digits)
    clip = read_clipboard()
    if clip and clip.isdigit():
        print(f"✓ Detected SID from clipboard: {clip}")
        return clip

    # 3. Console prompt
    if len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help'):
        print_usage()
        return None

    print_usage()
    print()
    print("Enter SID below (or press Ctrl+C to exit):")
    try:
        sid = input("SID: ").strip()
        return sid if sid else None
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def main() -> int:
    """Main entry point.

    Reads SID from command-line argument or prompts for console input.
    """
    sid = get_sid_from_args_or_input()

    if not sid:
        return 0

    # Basic SID validation
    if not sid.isdigit():
        print(f"Error: SID must be a number, got: {sid}")
        return 1

    try:
        return process_by_sid(sid)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
