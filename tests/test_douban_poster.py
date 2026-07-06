# -*- coding: utf-8 -*-
"""
Tests for Douban poster fetching utilities
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.douban_poster import (
    DoubanPosterParser,
    parse_posters_result,
    download_poster,
    _is_chinese_region,
    filter_and_sort_posters
)


# Sample HTML structure matching actual Douban photos page
SAMPLE_DOUBAN_HTML = '''
<li data-id="1108070214" class="">
    <div class="cover">
        <a href="https://movie.douban.com/photos/photo/1108070214/">
            <img src="https://img9.doubanio.com/view/photo/m/public/p1108070214.webp" />
        </a>
    </div>
    <div class="name">
        正式海报 美国
        <a href="https://movie.douban.com/photos/photo/1108070214/#comments">9回应</a>
    </div>
</li>

<li data-id="2376947864" class="">
    <div class="cover">
        <a href="https://movie.douban.com/photos/photo/2376947864/">
            <img src="https://img9.doubanio.com/view/photo/m/public/p2376947864.webp" />
        </a>
    </div>
    <div class="name">
        正式海报 中国大陆
        <a href="https://movie.douban.com/photos/photo/2376947864/#comments">3回应</a>
    </div>
</li>

<li data-id="2590737952" class="last">
    <div class="cover">
        <a href="https://movie.douban.com/photos/photo/2590737952/">
            <img src="https://img3.doubanio.com/view/photo/m/public/p2590737952.webp" />
        </a>
    </div>
    <div class="name">
        正式海报
        <a href="https://movie.douban.com/photos/photo/2590737952/#comments">1回应</a>
    </div>
</li>
'''


class TestDoubanPosterParser:
    """Tests for DoubanPosterParser class"""

    def test_parse_empty_html(self):
        """Test parsing with empty HTML returns empty list"""
        parser = DoubanPosterParser("")
        result = parser.parse()
        assert result == []

    def test_parse_none_html(self):
        """Test parsing with None HTML returns empty list"""
        parser = DoubanPosterParser(None)
        result = parser.parse()
        assert result == []

    def test_parse_valid_posters(self):
        """Test parsing HTML with actual Douban poster structure"""
        parser = DoubanPosterParser(SAMPLE_DOUBAN_HTML)
        result = parser.parse()

        assert len(result) == 3
        assert result[0]['title'] == '正式海报 美国'
        assert result[1]['title'] == '正式海报 中国大陆'
        assert result[2]['title'] == '正式海报'
        assert '/l/' in result[0]['original']  # Should convert to original URL

    def test_parse_poster_with_chinese_region(self):
        """Test parsing poster with Chinese region in title"""
        html_content = '''
        <li data-id="123456">
            <div class="cover">
                <a href="https://movie.douban.com/photos/photo/123456/">
                    <img src="https://img9.doubanio.com/view/photo/m/public/p123456.webp" />
                </a>
            </div>
            <div class="name">
                正式海报 中国香港
                <a href="#">2回应</a>
            </div>
        </li>
        '''
        parser = DoubanPosterParser(html_content)
        result = parser.parse()

        assert len(result) == 1
        assert result[0]['title'] == '正式海报 中国香港'

    def test_parse_poster_without_response_count(self):
        """Test parsing poster without response count"""
        html_content = '''
        <li data-id="789">
            <div class="cover">
                <a href="https://movie.douban.com/photos/photo/789/">
                    <img src="https://img9.doubanio.com/view/photo/m/public/p789.webp" />
                </a>
            </div>
            <div class="name">
                正式海报 日本
            </div>
        </li>
        '''
        parser = DoubanPosterParser(html_content)
        result = parser.parse()

        assert len(result) == 1
        assert result[0]['title'] == '正式海报 日本'

    def test_get_original_url_conversion(self):
        """Test URL conversion from thumbnail to original"""
        # Test m variant (webp) -> should convert /m/ to /l/
        url = "https://img9.doubanio.com/view/photo/m/public/p123456.webp"
        result = DoubanPosterParser._get_original_url(url)
        assert '/l/' in result
        assert '/m/' not in result  # /m/ should be replaced with /l/

        # Test s_ratio_poster -> should convert to /l/
        url = "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p123.jpg"
        result = DoubanPosterParser._get_original_url(url)
        assert '/l/' in result
        assert 's_ratio_poster' not in result

        # Test HTTPS conversion from protocol-relative URL
        url = "//img9.doubanio.com/view/photo/m/public/p123.webp"
        result = DoubanPosterParser._get_original_url(url)
        assert result.startswith('https:')


class TestParsePostersResult:
    """Tests for parse_posters_result function"""

    def test_parse_valid_html(self):
        """Test parsing valid HTML content with actual Douban structure"""
        result = parse_posters_result(SAMPLE_DOUBAN_HTML)
        assert len(result) == 3
        assert '正式海报' in result[0]['title']


class TestChineseRegionFilter:
    """Tests for Chinese region filtering"""

    def test_is_chinese_region_mainland(self):
        """Test detection of mainland China"""
        assert _is_chinese_region('正式海报 中国大陆') is True

    def test_is_chinese_region_hong_kong(self):
        """Test detection of Hong Kong"""
        assert _is_chinese_region('正式海报 中国香港') is True

    def test_is_chinese_region_taiwan(self):
        """Test detection of Taiwan"""
        assert _is_chinese_region('正式海报 中国台湾') is True

    def test_is_chinese_region_usa(self):
        """Test detection of non-Chinese region"""
        assert _is_chinese_region('正式海报 美国') is False

    def test_is_chinese_region_japan(self):
        """Test detection of non-Chinese region"""
        assert _is_chinese_region('正式海报 日本') is False


class TestFilterAndSortPosters:
    """Tests for filter_and_sort_posters function"""

    @patch('utils.douban_poster._get_image_size')
    def test_filter_by_keyword(self, mock_size):
        """Test filtering by keyword"""
        mock_size.return_value = 1000000

        posters = [
            {'title': '正式海报 中国大陆', 'original': 'http://example.com/1.jpg'},
            {'title': '剧照 中国大陆', 'original': 'http://example.com/2.jpg'},
            {'title': '正式海报 美国', 'original': 'http://example.com/3.jpg'},
        ]

        result = filter_and_sort_posters(posters, title_keyword='正式海报')
        assert len(result) == 2
        assert all('正式海报' in p['title'] for p in result)

    @patch('utils.douban_poster._get_image_size')
    def test_sort_by_size(self, mock_size):
        """Test sorting by size (largest first)"""
        def get_size(url):
            sizes = {
                'http://example.com/1.jpg': 500000,
                'http://example.com/2.jpg': 2000000,
                'http://example.com/3.jpg': 100000,
            }
            return sizes.get(url, 0)
        mock_size.side_effect = get_size

        posters = [
            {'title': '正式海报 中国大陆', 'original': 'http://example.com/1.jpg'},
            {'title': '正式海报 美国', 'original': 'http://example.com/2.jpg'},
            {'title': '正式海报 日本', 'original': 'http://example.com/3.jpg'},
        ]

        result = filter_and_sort_posters(posters, title_keyword='正式海报')
        # Should be sorted by size: 2MB, 500KB, 100KB
        assert result[0]['original'] == 'http://example.com/2.jpg'
        assert result[1]['original'] == 'http://example.com/1.jpg'
        assert result[2]['original'] == 'http://example.com/3.jpg'


class TestDownloadPoster:
    """Tests for download_poster function"""

    @patch('utils.douban_poster.requests.get')
    def test_download_success(self, mock_get):
        """Test successful poster download"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'fake image data']
        mock_get.return_value = mock_response

        with patch('builtins.open', MagicMock()):
            result = download_poster(
                'https://img9.doubanio.com/view/photo/l/public/p123.jpg',
                '/tmp/test_poster.jpg'
            )
            assert result is True

    @patch('utils.douban_poster.requests.get')
    def test_download_failure(self, mock_get):
        """Test failed poster download"""
        mock_get.side_effect = Exception("Network error")

        result = download_poster(
            'https://img9.doubanio.com/view/photo/l/public/p123.jpg',
            '/tmp/test_poster.jpg'
        )
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
