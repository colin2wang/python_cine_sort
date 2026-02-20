# Python Cine Sort - Douban Movie Information Toolkit

A comprehensive Python toolkit for automated movie file organization and Douban movie information retrieval with intelligent parsing capabilities.

## Key Features

- 🎬 **Intelligent Movie Search**: Advanced Douban movie querying with automatic verification bypass
- 📊 **Smart Information Parsing**: Sophisticated HTML content parsing with regex-based extraction
- 🔧 **Robust Error Handling**: Comprehensive exception management and retry mechanisms
- 🌐 **Multi-language Support**: Native support for Chinese movie names and international titles
- 📁 **Advanced File Scanning**: Intelligent movie file detection with configurable pattern matching
- 🔄 **Anti-bot Automation**: Built-in Proof of Work (PoW) system for automatic Douban verification bypass
- ⚙️ **Flexible Configuration**: YAML-based configuration system for easy customization
- 📝 **Comprehensive Logging**: Detailed logging with multiple output formats and levels

## Project Architecture

```
python_cine_sort/
├── utils/                      # Core utility modules
│   ├── __init__.py
│   ├── common_util.py          # Shared utility functions and helpers
│   ├── douban_details.py       # Detailed movie information retrieval
│   ├── douban_search.py        # Core Douban search functionality
│   ├── logging_util.py         # Advanced logging system
│   └── movie_filename_util.py  # Movie file scanning and parsing
├── test/                       # Comprehensive test suite
│   ├── test_douban_details.py
│   ├── test_douban_search.py
│   ├── test_movie_filename_util.py
│   ├── test_movie_full_process.py
│   └── test_parse_movie_info_from_file.py
├── test_data/                  # Test data and fixtures
│   └── douban_search_result.html
├── configs/                    # Configuration files
│   └── movie_filename_util.yml
├── douban_query_url.md         # Detailed Douban API documentation
├── pyproject.toml              # Project configuration and dependencies
└── uv.lock                    # Dependency lock file
```

## Quick Start

### Prerequisites
- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd python_cine_sort

# Install dependencies using uv (recommended)
uv sync

# Alternative: Install using pip
pip install requests>=2.32.5 beautifulsoup4>=4.14.3 pyyaml>=6.0
```

### Configuration Setup

Create a configuration file at `configs/movie_filename_util.yml`:

```yaml
extensions:
  - .mkv
  - .mp4
  - .avi
  - .mov

cleanup_patterns:
  - '\[.*?\]'                     # Remove bracketed content
  - '\(.*?\)'                     # Remove parenthetical content
  - '1080[Pp]|720[Pp]|4[Kk]'      # Remove resolution indicators
  - 'HD|BD|DVD|BluRay'            # Remove quality indicators
  - '[Cc]hi|[Ee]ng'               # Remove language indicators

tech_patterns:
  - 'x264|x265|HEVC|AVC'          # Video codecs
  - 'AAC|AC3|DTS'                 # Audio codecs
  - 'HDR|SDR'                     # Dynamic range

language_patterns:
  - 'Chinese|English|Japanese'    # Language tags
  - 'Dubbed|Subbed'               # Audio/subtitle info

year_pattern: '(?:19|20)\d{2}'    # Year extraction pattern
```

## Core Functionality

### 1. Douban Movie Search

Query movie information from Douban with automatic verification handling:

```python
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result

# Search for movie information
html_content = get_movie_search_result_html("肖申克的救赎", "1994")

if html_content:
    # Parse structured movie information
    movie_info = parse_movie_search_result(html_content)
    print(f"Title: {movie_info['title']}")
    print(f"Rating: {movie_info['rating']}")
    print(f"Directors: {movie_info['directors']}")
    print(f"Actors: {movie_info['actors']}")
```

### 2. Movie File Scanning

Intelligent movie file detection and metadata extraction:

```python
from pathlib import Path
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig

# Load configuration
config_path = Path("configs/movie_file_util.yml")
config = MovieFileScannerConfig(config_path)
scanner = MovieFileScanner(config)

# Scan directory for movie files
movies = scanner.scan_directory(Path("/path/to/movies"))

for movie in movies:
    print(f"File: {movie.raw_filename}")
    print(f"Movie Name: {movie.movie_name}")
    print(f"Year: {movie.year}")
    print(f"Path: {movie.file_path}")
```

### 3. Complete Processing Pipeline

End-to-end movie organization workflow:

```python
from utils import get_movie_search_result_html, parse_movie_search_result

# Process all movies in a directory
for movie_file in movies:
    # Search for movie information
    html_result = get_movie_search_result_html(
        movie_file.movie_name, 
        movie_file.year
    )
    
    if html_result:
        # Parse and enrich movie metadata
        movie_info = parse_movie_search_result(html_result)
        
        # Use parsed information for organization
        print(f"Organizing: {movie_info['title']} ({movie_info['year']})")
        print(f"Rating: {movie_info['rating']}/10 from {movie_info['review_count']} reviews")
```

### 4. Running Tests

Execute the comprehensive test suite:

```bash
# Run all tests
python -m unittest discover test/

# Run specific test modules
python test/test_douban_search.py
python test/test_movie_file_util.py
python test/test_movie_full_process.py

# Run with verbose output
python -m unittest discover test/ -v
```

## Module Reference

### Douban Search Module (`utils/douban_search.py`)

Core functions for Douban movie querying and parsing:

- `get_movie_search_result_html(name: str, year: str) -> Optional[str]`
  - Performs HTTP requests to Douban search API
  - Handles anti-bot verification automatically
  - Returns raw HTML content for further processing

- `parse_movie_search_result(html_content: str) -> dict`
  - Extracts structured movie information using regex patterns
  - Parses title, rating, cast, year, and description
  - Handles edge cases and malformed responses

### Movie Filename Utility (`utils/movie_filename_util.py`)

Advanced file scanning and metadata extraction:

- `MovieFileScannerConfig`: YAML-based configuration management
- `MovieFileScanner`: Main scanning engine with pattern matching
- `MovieFileInfo`: Data class for structured movie file metadata
- `_process_movie_name()`: Sophisticated filename cleaning pipeline
- `_extract_year()`: Reliable year extraction from filenames

### Logging Utility (`utils/logging_util.py`)

Production-ready logging system:

- Multi-handler support (console, file, rotating)
- Configurable log levels and formatting
- Structured logging with contextual information
- Performance-optimized for high-volume operations

### Common Utilities (`utils/common_util.py`)

Shared helper functions:

- `sleep_for_random_time()`: Randomized delays for rate limiting
- Network utility functions
- String processing helpers
- Error handling utilities

## Advanced Configuration

### Pattern Matching System

The scanner uses a sophisticated pattern matching system for accurate movie name extraction:

```yaml
# Advanced configuration example
extensions:
  - .mkv
  - .mp4
  - .avi
  - .mov
  - .wmv

cleanup_patterns:
  - '\[(.*?)\]'                       # Bracketed groups
  - '\((.*?)\)'                       # Parenthetical content
  - '\{(.*?)\}'                       # Curly brace content
  - '1080[Pp]|720[Pp]|4[Kk]|8[Kk]'    # Resolution tags
  - 'HD|BD|DVD|BluRay|WEB-DL'         # Quality indicators
  - 'HDR|SDR|DV'                      # Dynamic range

tech_patterns:
  - 'x264|x265|h264|h265|HEVC|AVC'    # Video codecs
  - 'AAC|AC3|DTS|FLAC|DD|DDP'         # Audio codecs
  - 'H264|H\.264|H265|H\.265'       # Alternative codec formats

language_patterns:
  - 'Chinese|中文|国语|粤语'              # Chinese language variants
  - 'English|英文'                     # English indicators
  - 'Japanese|日语|日文'                # Japanese indicators
  - 'Dubbed|配音版|中字|字幕'            # Dubbing/subtitle info

year_pattern: '(?:19|20)\d{2}'
```

### Performance Tuning

Adjust scanner behavior for different environments:

```yaml
# Performance configuration
performance:
  max_workers: 4                    # Concurrent processing threads
  chunk_size: 100                   # Files per processing batch
  timeout: 30                       # Network timeout in seconds

logging:
  level: INFO                       # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s [%(levelname)s] %(message)s"
  file_output: true
  max_file_size: 10MB
```

## Technical Highlights

### Robust Architecture

- **Type Safety**: Full type hint coverage for improved IDE support
- **Error Resilience**: Comprehensive exception handling with graceful degradation
- **Modular Design**: Clean separation of concerns with well-defined interfaces
- **Performance Optimized**: Efficient regex compilation and pattern caching

### Smart Processing Pipeline

1. **File Discovery**: Recursive directory scanning with extension filtering
2. **Pattern Cleanup**: Multi-stage regex-based filename sanitization
3. **Metadata Extraction**: Year detection and movie name isolation
4. **Douban Integration**: Automated search with verification bypass
5. **Information Parsing**: Structured data extraction from HTML responses
6. **Quality Validation**: Data integrity checks and fallback mechanisms

### Anti-Bot Intelligence

Built-in Proof of Work system that automatically:
- Detects Douban verification challenges
- Computes required proof values
- Submits verification responses
- Maintains session continuity
- Handles rate limiting gracefully

## Documentation

For detailed module documentation, please refer to the following guides:

- [Douban Details Documentation](docs/douban_details.md) - Comprehensive guide for parsing detailed movie information from Douban
- [Douban Search Documentation](docs/douban_search.md) - Complete reference for Douban movie search functionality
- [Movie File Utility Documentation](docs/movie_file_util.md) - Detailed guide for movie file scanning and metadata extraction

## API Documentation

For detailed information about Douban API endpoints and parameters, see [douban_query_url.md](douban_query_url.md).

## Best Practices

### Responsible Usage

- **Rate Limiting**: Implement appropriate delays between requests
- **Terms Compliance**: Respect Douban's terms of service and robots.txt
- **Data Usage**: Use extracted information for personal organization only
- **Network Efficiency**: Cache results to minimize redundant requests

### Performance Optimization

- Configure appropriate thread counts for your system
- Use selective directory scanning for large collections
- Enable logging only at necessary levels in production
- Regular cleanup of temporary files and logs

## Development Status

✅ **Production Ready Features**:
- Movie file scanning and parsing
- Douban search integration
- HTML content parsing
- Anti-bot verification bypass
- Comprehensive test coverage
- Configuration management

🏗️ **Future Enhancements**:
- Database integration for persistent storage
- Web API for remote access
- Batch processing optimizations
- Advanced filtering capabilities
- Export/import functionality
- Mobile application interface

## Contributing Guidelines

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Ensure all tests pass (`python -m unittest discover`)
4. Add/update documentation as needed
5. Submit pull request with clear description

## License Information

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Douban for providing comprehensive movie database
- BeautifulSoup4 for reliable HTML parsing
- Python community for excellent libraries and tools
- Open source contributors who inspired this project

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