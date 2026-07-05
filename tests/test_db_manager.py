# -*- coding: utf-8 -*-
"""
Tests for database manager
"""
import os
import tempfile
import pytest
from pathlib import Path
from utils.db_manager import MovieDB


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = MovieDB(db_path)
        yield db
        db_path.unlink(missing_ok=True)


class TestMovieDB:

    def test_init_creates_db(self, temp_db):
        """Database file should be created on init."""
        assert temp_db.db_path.exists()

    def test_save_and_get_movie(self, temp_db):
        """Save a movie and retrieve it by SID."""
        details = {
            'sid': '12345',
            'title': '测试电影',
            'original_title': 'Test Movie',
            'year': '2024',
            'rating': '8.5',
            'rating_count': 1000,
            'description': 'A test movie.',
            'country': '中国大陆',
            'language': '汉语',
            'runtime': 120,
            'imdb_id': 'tt1234567',
            'directors': ['导演A'],
            'actors': ['演员1', '演员2'],
            'genres': ['剧情', '动作'],
            'release_dates': ['2024-01-01(中国大陆)'],
            'awards': [{'event': '金鸡奖', 'category': '最佳影片', 'recipient': '测试电影'}],
        }
        movie_id = temp_db.save_movie(details, directory_path='/movies/test')
        assert movie_id > 0

        movie = temp_db.get_movie_by_sid('12345')
        assert movie is not None
        assert movie['title'] == '测试电影'
        assert movie['original_title'] == 'Test Movie'
        assert movie['directors'] == ['导演A']
        assert movie['actors'] == ['演员1', '演员2']
        assert movie['genres'] == ['剧情', '动作']
        assert movie['release_dates'] == ['2024-01-01(中国大陆)']
        assert len(movie['awards']) == 1
        assert movie['directory_path'] == '/movies/test'

    def test_upsert_movie(self, temp_db):
        """Saving same SID twice should update, not duplicate."""
        details = {'sid': '99999', 'title': '原始标题', 'year': '2020'}
        temp_db.save_movie(details)

        details['title'] = '更新标题'
        temp_db.save_movie(details)

        movie = temp_db.get_movie_by_sid('99999')
        assert movie['title'] == '更新标题'

        movies = temp_db.get_all_movies()
        assert len(movies) == 1

    def test_save_and_get_posters(self, temp_db):
        """Save poster records and verify."""
        details = {'sid': '88888', 'title': '海报测试'}
        movie_id = temp_db.save_movie(details)

        posters = [
            {'title': '正式海报 中国大陆', 'original': 'https://img.doubanio.com/p1.webp',
             'thumbnail': 'https://img.doubanio.com/thumb.webp', 'size': 500000},
            {'title': '正式海报 美国', 'original': 'https://img.doubanio.com/p2.webp',
             'thumbnail': 'https://img.doubanio.com/thumb2.webp', 'size': 300000},
        ]
        count = temp_db.save_posters(movie_id, posters)
        assert count == 2

        movie = temp_db.get_movie_by_sid('88888')
        assert len(movie['posters']) == 2

    def test_get_nonexistent_movie(self, temp_db):
        """Query non-existent SID returns None."""
        assert temp_db.get_movie_by_sid('00000') is None

    def test_get_all_movies_empty(self, temp_db):
        """Empty database returns empty list."""
        assert temp_db.get_all_movies() == []

    def test_update_poster_download(self, temp_db):
        """Update poster download status."""
        details = {'sid': '77777', 'title': '下载测试'}
        movie_id = temp_db.save_movie(details)

        posters = [
            {'title': '正式海报', 'original': 'https://img.doubanio.com/p1.webp',
             'thumbnail': '', 'size': 100000},
        ]
        temp_db.save_posters(movie_id, posters)

        temp_db.update_poster_download(movie_id, 'https://img.doubanio.com/p1.webp', '/local/path.webp')
        movie = temp_db.get_movie_by_sid('77777')
        poster = movie['posters'][0]
        assert poster['is_downloaded'] == 1
        assert poster['local_path'] == '/local/path.webp'
