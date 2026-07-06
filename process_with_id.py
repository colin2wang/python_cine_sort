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
from utils.douban_poster import get_official_posters, download_official_posters, download_poster
from utils.movie_org_util import organize_movie_by_detail, MovieOrgConfig
from utils.db_manager import MovieDB
from utils.logging_config import setup_logger

logger = setup_logger(__name__)


def process_by_sid(sid: str) -> int:
    """Fetch Douban details for a SID and create organized directory.

    Checks the database first: if movie info and poster data already exist
    for this SID, uses the cached data instead of fetching from Douban.

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

    # Load organizer config to get movie_folder for display
    org_config = MovieOrgConfig(org_config_file)
    movie_folder = Path(org_config.movie_folder).resolve()
    print(f"Movie folder (from config): {movie_folder}")

    db = MovieDB()

    # Step 1: Check database first for existing data
    logger.info(f"Checking database for SID: {sid}")
    db_movie = db.get_movie_by_sid(sid)

    if db_movie and db_movie.get('title') and db_movie.get('posters'):
        logger.info(f"✓ Found cached data in database: {db_movie.get('title')}")
        logger.info(f"  Chinese Title: {db_movie.get('title', 'N/A')}")
        logger.info(f"  Original Title: {db_movie.get('original_title', 'N/A')}")
        logger.info(f"  Year: {db_movie.get('year', 'N/A')}")
        logger.info(f"  Rating: {db_movie.get('rating', 'N/A')}")
        logger.info(f"  Directors: {', '.join(db_movie.get('directors', [])[:3])}")

        # Use cached movie data for directory creation
        movie_details = db_movie
        movie_details['sid'] = sid

        # Check if directory already exists
        existing_dir = db_movie.get('directory_path')
        if existing_dir and Path(existing_dir).exists():
            logger.info(f"✓ Directory already exists: {existing_dir}")
            movie_dir = existing_dir
        else:
            # Create directory using cached data
            logger.info("Creating organized directory structure...")
            movie_dir = organize_movie_by_detail(
                movie_details,
                config_file=str(org_config_file)
            )
            if not movie_dir:
                logger.error("✗ Failed to create directory")
                return 1
            # Update database with new directory path
            db.save_movie(movie_details, directory_path=str(movie_dir))

        print(f"✓ Movie directory: {movie_dir}")

        # Check poster download status
        posters = db_movie.get('posters', [])
        downloaded_count = sum(1 for p in posters if p.get('is_downloaded'))
        not_downloaded = [p for p in posters if not p.get('is_downloaded')]

        if downloaded_count > 0:
            logger.info(f"✓ {downloaded_count} posters already downloaded")

        poster_dir = Path(movie_dir)

        # Download missing posters (with re-fetch on failure)
        if not_downloaded:
            logger.info(f"Downloading {len(not_downloaded)} missing posters...")
            failed_urls = set()

            for poster in not_downloaded:
                original_url = poster.get('original_url', '')
                if not original_url or original_url in failed_urls:
                    continue

                # Build filename with keyword/region tags
                url_filename = original_url.split('/')[-1]
                if '.' in url_filename:
                    base_name, ext = url_filename.rsplit('.', 1)
                    ext = f".{ext}"
                else:
                    base_name = url_filename
                    ext = ".jpg"

                keyword = poster.get('keyword', '')
                region = poster.get('region', '')
                if not keyword and poster.get('title'):
                    title_parts = poster['title'].strip().split()
                    keyword = title_parts[0] if title_parts else ''
                    region = title_parts[1] if len(title_parts) > 1 else ''

                if keyword and region:
                    filename = f"{base_name}_{keyword}_{region}{ext}"
                elif keyword:
                    filename = f"{base_name}_{keyword}{ext}"
                else:
                    filename = f"{base_name}{ext}"

                save_path = str(poster_dir / filename)

                if download_poster(original_url, save_path):
                    db.update_poster_download(
                        movie_id=db_movie['id'],
                        original_url=original_url,
                        local_path=save_path
                    )
                    logger.info(f"  - Downloaded: {filename}")
                else:
                    failed_urls.add(original_url)
                    logger.warning(f"  - Failed: {original_url}")

            # Re-fetch poster metadata from Douban for any that failed
            if failed_urls:
                logger.info("Re-fetching poster metadata from Douban for failed URLs...")
                fresh_posters = get_official_posters(sid)
                if fresh_posters:
                    # Delete stale poster records with failed URLs
                    db.delete_posters_by_urls(db_movie['id'], list(failed_urls))
                    # Save fresh metadata (even if downloads may fail)
                    db.save_posters(db_movie['id'], fresh_posters)
                    logger.info(f"✓ Saved {len(fresh_posters)} fresh poster records to database")

                    for poster in fresh_posters:
                        fresh_url = poster.get('original', poster.get('original_url', ''))
                        if not fresh_url:
                            continue
                        title = poster.get('title', '')
                        url_fn = fresh_url.split('/')[-1]
                        if '.' in url_fn:
                            fresh_base, fresh_ext = url_fn.rsplit('.', 1)
                            fresh_ext = f".{fresh_ext}"
                        else:
                            fresh_base = url_fn
                            fresh_ext = ".jpg"

                        title_parts = title.strip().split()
                        fresh_keyword = title_parts[0] if title_parts else ''
                        fresh_region = title_parts[1] if len(title_parts) > 1 else ''

                        if fresh_keyword and fresh_region:
                            fresh_filename = f"{fresh_base}_{fresh_keyword}_{fresh_region}{fresh_ext}"
                        elif fresh_keyword:
                            fresh_filename = f"{fresh_base}_{fresh_keyword}{fresh_ext}"
                        else:
                            fresh_filename = f"{fresh_base}{fresh_ext}"

                        fresh_save_path = str(poster_dir / fresh_filename)
                        if download_poster(fresh_url, fresh_save_path):
                            db.update_poster_download(
                                movie_id=db_movie['id'],
                                original_url=fresh_url,
                                local_path=fresh_save_path
                            )
                            logger.info(f"  - Re-downloaded: {fresh_filename}")

        # Cleanup: remove downloaded files not tracked in database
        all_posters = db.get_movie_by_sid(sid)
        if all_posters:
            db_files = set()
            for p in all_posters.get('posters', []):
                lp = p.get('local_path', '')
                if lp and Path(lp).exists():
                    db_files.add(Path(lp).resolve())
            if poster_dir.exists():
                for f in poster_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                        if f.resolve() not in db_files:
                            logger.info(f"  - Removing orphaned file: {f.name}")
                            f.unlink()

        return 0

    # Step 2: Cache miss — fetch from Douban
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

    logger.info("✓ Successfully parsed movie details:")
    logger.info(f"  Chinese Title: {movie_details.get('title', 'N/A')}")
    logger.info(f"  Original Title: {movie_details.get('original_title', 'N/A')}")
    logger.info(f"  Year: {movie_details.get('year', 'N/A')}")
    logger.info(f"  Rating: {movie_details.get('rating', 'N/A')}")
    logger.info(f"  Directors: {', '.join(movie_details.get('directors', [])[:3])}")

    # Ensure SID is set in details
    if 'sid' not in movie_details:
        movie_details['sid'] = sid

    # Step 3: Create organized directory structure
    logger.info("Creating organized directory structure...")
    movie_dir = organize_movie_by_detail(
        movie_details,
        config_file=str(org_config_file)
    )

    if not movie_dir:
        logger.error("✗ Failed to create directory")
        return 1

    print(f"✓ Successfully created directory: {movie_dir}")

    # Step 4: Download official posters
    logger.info("Downloading official posters...")
    poster_dir = Path(movie_dir)
    downloaded_posters = download_official_posters(
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

    # Step 5: Save to database
    logger.info("Saving to database...")
    try:
        movie_id = db.save_movie(movie_details, directory_path=str(movie_dir))
        logger.info(f"✓ Saved movie to database (ID: {movie_id})")

        # Get poster metadata and save
        poster_metadata = get_official_posters(sid)
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
