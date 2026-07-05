"""SQLite database manager for movie and poster data."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from utils.logging_config import setup_logger

logger = setup_logger(__name__)

DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "cine_sort.db"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sid TEXT UNIQUE NOT NULL,
    title TEXT,
    original_title TEXT,
    aliases TEXT,
    year TEXT,
    rating TEXT,
    rating_count INTEGER,
    description TEXT,
    country TEXT,
    language TEXT,
    runtime INTEGER,
    imdb_id TEXT,
    top250_rank INTEGER,
    short_comments_count INTEGER,
    reviews_count INTEGER,
    poster_url TEXT,
    directory_path TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS directors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS actors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS release_dates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    date_text TEXT NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    event TEXT,
    category TEXT,
    recipient TEXT,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS posters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    poster_id TEXT,
    title TEXT,
    keyword TEXT,
    region TEXT,
    thumbnail_url TEXT,
    original_url TEXT,
    file_size INTEGER,
    is_downloaded INTEGER DEFAULT 0,
    local_path TEXT,
    created_at TEXT,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    UNIQUE(movie_id, original_url)
);
"""


class MovieDB:
    """SQLite database manager for movie and poster data."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        try:
            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
        finally:
            conn.close()

    def save_movie(self, movie_details: Dict[str, Any], directory_path: str = None) -> int:
        """Save movie and all related data. Returns movie id."""
        now = datetime.now().isoformat()
        sid = movie_details.get('sid', '')

        conn = self._get_conn()
        try:
            # Upsert movie
            existing = conn.execute("SELECT id FROM movies WHERE sid = ?", (sid,)).fetchone()
            if existing:
                movie_id = existing['id']
                conn.execute("""
                    UPDATE movies SET title=?, original_title=?, aliases=?, year=?,
                        rating=?, rating_count=?, description=?, country=?, language=?,
                        runtime=?, imdb_id=?, top250_rank=?, short_comments_count=?,
                        reviews_count=?, poster_url=?, directory_path=?, updated_at=?
                    WHERE id=?
                """, (
                    movie_details.get('title'),
                    movie_details.get('original_title'),
                    movie_details.get('aliases'),
                    movie_details.get('year'),
                    movie_details.get('rating'),
                    movie_details.get('rating_count'),
                    movie_details.get('description'),
                    movie_details.get('country'),
                    movie_details.get('language'),
                    movie_details.get('runtime'),
                    movie_details.get('imdb_id'),
                    movie_details.get('top250_rank'),
                    movie_details.get('short_comments_count'),
                    movie_details.get('reviews_count'),
                    movie_details.get('poster_url'),
                    directory_path,
                    now,
                    movie_id,
                ))
                # Delete old related data
                for table in ('directors', 'actors', 'genres', 'release_dates', 'awards', 'posters'):
                    conn.execute(f"DELETE FROM {table} WHERE movie_id = ?", (movie_id,))
            else:
                cur = conn.execute("""
                    INSERT INTO movies (sid, title, original_title, aliases, year,
                        rating, rating_count, description, country, language,
                        runtime, imdb_id, top250_rank, short_comments_count,
                        reviews_count, poster_url, directory_path, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    sid,
                    movie_details.get('title'),
                    movie_details.get('original_title'),
                    movie_details.get('aliases'),
                    movie_details.get('year'),
                    movie_details.get('rating'),
                    movie_details.get('rating_count'),
                    movie_details.get('description'),
                    movie_details.get('country'),
                    movie_details.get('language'),
                    movie_details.get('runtime'),
                    movie_details.get('imdb_id'),
                    movie_details.get('top250_rank'),
                    movie_details.get('short_comments_count'),
                    movie_details.get('reviews_count'),
                    movie_details.get('poster_url'),
                    directory_path,
                    now,
                    now,
                ))
                movie_id = cur.lastrowid

            # Insert directors
            for name in movie_details.get('directors', []):
                conn.execute("INSERT INTO directors (movie_id, name) VALUES (?, ?)", (movie_id, name))

            # Insert actors
            for name in movie_details.get('actors', []):
                conn.execute("INSERT INTO actors (movie_id, name) VALUES (?, ?)", (movie_id, name))

            # Insert genres
            for name in movie_details.get('genres', []):
                conn.execute("INSERT INTO genres (movie_id, name) VALUES (?, ?)", (movie_id, name))

            # Insert release dates
            for date_text in movie_details.get('release_dates', []):
                conn.execute("INSERT INTO release_dates (movie_id, date_text) VALUES (?, ?)", (movie_id, date_text))

            # Insert awards
            for award in movie_details.get('awards', []):
                conn.execute(
                    "INSERT INTO awards (movie_id, event, category, recipient) VALUES (?,?,?,?)",
                    (movie_id, award.get('event'), award.get('category'), award.get('recipient'))
                )

            conn.commit()
            logger.info(f"Saved movie: {movie_details.get('title')} (SID: {sid}, ID: {movie_id})")
            return movie_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save movie (SID: {sid}): {e}")
            raise
        finally:
            conn.close()

    def save_posters(self, movie_id: int, posters: List[Dict[str, Any]]) -> int:
        """Save poster records. Returns count inserted."""
        now = datetime.now().isoformat()
        count = 0
        conn = self._get_conn()
        try:
            for poster in posters:
                title = poster.get('title', '')
                title_parts = title.strip().split()
                keyword = title_parts[0] if title_parts else ''
                region = title_parts[1] if len(title_parts) > 1 else ''

                # Extract poster_id from URL
                original_url = poster.get('original', poster.get('original_url', ''))
                url_filename = original_url.split('/')[-1] if original_url else ''
                poster_id = url_filename.split('.')[0] if '.' in url_filename else url_filename

                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO posters
                            (movie_id, poster_id, title, keyword, region,
                             thumbnail_url, original_url, file_size, is_downloaded,
                             local_path, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        movie_id,
                        poster_id,
                        title,
                        keyword,
                        region,
                        poster.get('thumbnail', poster.get('thumbnail_url', '')),
                        original_url,
                        poster.get('size', poster.get('file_size', 0)),
                        1 if poster.get('local_path') else 0,
                        poster.get('local_path'),
                        now,
                    ))
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # duplicate poster_url, skip

            conn.commit()
            logger.info(f"Saved {count} posters for movie_id={movie_id}")
            return count
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save posters: {e}")
            raise
        finally:
            conn.close()

    def update_poster_download(self, movie_id: int, original_url: str, local_path: str):
        """Mark a poster as downloaded and set its local path."""
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE posters SET is_downloaded=1, local_path=? WHERE movie_id=? AND original_url=?",
                (local_path, movie_id, original_url)
            )
            conn.commit()
        finally:
            conn.close()

    def get_movie_by_sid(self, sid: str) -> Optional[Dict[str, Any]]:
        """Fetch full movie data by SID."""
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM movies WHERE sid = ?", (sid,)).fetchone()
            if not row:
                return None

            movie = dict(row)
            movie['directors'] = [r['name'] for r in conn.execute("SELECT name FROM directors WHERE movie_id=?", (row['id'],))]
            movie['actors'] = [r['name'] for r in conn.execute("SELECT name FROM actors WHERE movie_id=?", (row['id'],))]
            movie['genres'] = [r['name'] for r in conn.execute("SELECT name FROM genres WHERE movie_id=?", (row['id'],))]
            movie['release_dates'] = [r['date_text'] for r in conn.execute("SELECT date_text FROM release_dates WHERE movie_id=?", (row['id'],))]
            movie['awards'] = [dict(r) for r in conn.execute("SELECT event, category, recipient FROM awards WHERE movie_id=?", (row['id'],))]
            movie['posters'] = [dict(r) for r in conn.execute("SELECT * FROM posters WHERE movie_id=?", (row['id'],))]
            return movie
        finally:
            conn.close()

    def get_all_movies(self) -> List[Dict[str, Any]]:
        """Fetch all movies with basic info."""
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT id, sid, title, original_title, year, rating, directory_path FROM movies ORDER BY id").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
