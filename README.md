# Python Douban Movie Sorting Tool

This is a Python toolkit for querying and processing Douban movie information.

## Features

- 🎬 Douban movie search and query
- 📊 Movie information parsing (under development)
- 🔧 Robust error handling mechanism
- 🌐 Support for Chinese movie name queries
- 📁 Movie file scanning and organization
- 🔄 Automated Douban verification bypass (Proof of Work)

## Project Structure

```
python_cine_sort/
├── utils/
│   ├── __init__.py
│   ├── common_util.py          # Common utility functions
│   ├── douban_details.py       # Douban movie details module
│   ├── douban_search.py        # Douban search core module
│   ├── logging_util.py         # Logging utilities
│   └── movie_file_util.py      # Movie file scanner
├── test/
│   ├── test_douban_details.py
│   ├── test_douban_details_pow.py
│   ├── test_douban_search.py
│   ├── test_movie_file_util.py
│   ├── test_movie_full_process.py
│   └── test_parse_movie_info_from_file.py
├── test_data/
│   └── douban_search_result.html
├── configs/
│   └── movie_file_util.yml
├── pyproject.toml              # Project configuration
└── uv.lock                    # Dependency lock file
```

## Installation

```bash
# Install dependencies using uv
uv sync

# Or install using pip
pip install requests>=2.32.5 beautifulsoup4>=4.14.3 pyyaml>=6.0
```

## Usage

### Basic Usage

```python
from utils.douban_search import get_movie_search_result_html

# Query movie information
html_content = get_movie_search_result_html("The Shawshank Redemption", "1994")
if html_content:
    print(f"Obtained {len(html_content)} characters of content")
```

### Movie File Scanning

```python
from utils.movie_filename_util import scan_movies_from_directory

# Scan movie files from directory
movies = scan_movies_from_directory("/path/to/movies")
for movie in movies:
    print(f"Movie: {movie['movie_name']} ({movie['year']})")
```

### Running Tests

```bash
# Run Douban query tests
python test/test_douban_search.py

# Run movie scanner tests
python test/test_movie_filename_util.py

# Run full process tests
python test/test_movie_full_process.py

# Run Douban verification bypass tests
python test/test_douban_details_pow.py
```

## Core Modules

### Douban Search (`utils/douban_search.py`)
- `get_movie_search_result_html()`: Fetch movie search results from Douban
- `parse_movie_search_result()`: Parse movie information from search results

### Movie File Scanner (`utils/movie_file_util.py`)
- `MovieFileScanner`: Main scanner class for movie files
- `MovieFileScannerConfig`: Configuration class for scanner settings
- `scan_movies_from_directory()`: Convenience function for directory scanning

### Logging Utilities (`utils/logging_util.py`)
- Comprehensive logging configuration
- Multiple log levels and output formats
- File and console logging support

## Configuration

The movie file scanner can be configured using YAML files:

```yaml
# Sample configuration in configs/movie_filename_util.yml
extensions:
  - .mkv
  - .mp4
  - .avi

cleanup_rules:
  - '1080[Pp]|720[Pp]|4[Kk]'           # Resolution indicators
  - 'HD|BD|DVD'                       # Quality indicators
  - '[Cc]hi|[Ee]ng'                   # Language indicators

year_patterns:
  - '(?:^|\s)(19|20)\d{2}(?:$|\s)'    # Year pattern matching
```

## Key Improvements

### Fixed Issues:
1. **Function name typos**: `get_moive` → `get_movie`
2. **String formatting**: Modern f-string instead of old % formatting
3. **Missing return values**: Added complete return logic
4. **Incomplete error handling**: Enhanced detailed exception handling
5. **Missing type hints**: Added typing annotations
6. **Documentation strings**: Improved function documentation

### New Features:
1. **Timeout control**: 10-second request timeout
2. **Encoding handling**: Proper UTF-8 encoding
3. **Detailed logging**: Clear success/failure feedback
4. **Extensible design**: Reserved movie information parsing interface
5. **Advanced file parsing**: Sophisticated filename cleanup and movie name extraction
6. **Proof of Work**: Automatic Douban verification bypass

## Important Notes

- This tool is intended for learning and research purposes only
- Please comply with Douban website terms of service
- Recommend controlling request frequency to avoid server pressure
- Returned content is raw HTML; structured data requires further parsing
- Some advanced features may require additional configuration

## Development Roadmap

- [ ] Implement HTML content parsing functionality
- [ ] Add movie ratings and detailed information extraction
- [ ] Support batch queries and export functionality
- [ ] Add caching mechanism to improve efficiency
- [ ] Enhance unit test coverage
- [ ] Add GUI interface for easier usage

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License

## Acknowledgments

- Thanks to Douban for providing the movie database
- Inspired by various movie organization tools
- Built with Python best practices and modern development tools