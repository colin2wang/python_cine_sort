# Movie Filename Utility Documentation

This document describes the usage and return formats of the movie filename scanning functionality in `movie_filename_util.py`, using the actual configuration from `configs/movie_filename_util.yml`.

## Overview

The module provides utilities for scanning video files in directories and extracting structured movie information from filenames, including movie names and release years. It uses comprehensive pattern matching to clean up filenames and extract meaningful information.

## Core Components

### 1. MovieFileInfo (Data Class)

Represents parsed movie file information.

#### Fields Structure
```python
@dataclass
class MovieFileInfo:
    file_path: Path      # Full path to the movie file
    movie_name: str      # Extracted movie title/name
    year: Optional[str]  # Release year (if found)
    extension: str       # File extension (e.g., ".mp4", ".mkv")
    raw_filename: str    # Original filename with extension
```

#### Example Instance
```python
MovieFileInfo(
    file_path=Path("/movies/Inception.2010.1080p.BluRay.x264.mp4"),
    movie_name="Inception",
    year="2010",
    extension=".mp4",
    raw_filename="Inception.2010.1080p.BluRay.x264.mp4"
)
```

### 2. Configuration System

The scanner uses `configs/movie_filename_util.yml` for pattern definitions:

#### File Extensions Supported
```yaml
extensions:
  - .mkv
  - .mp4
  - .avi
  - .mov
  - .wmv
  - .flv
  - .webm
```

#### Cleanup Patterns
Removes unwanted elements from filenames:
- Brackets and parentheses: `[.*?]`, `(.*?)`
- Website domains and sources
- Resolution and quality markers (HD, BD, DVD, etc.)
- Years in various contexts
- File/audio formats
- HDR and video technologies
- Release groups
- Leading/trailing separators

#### Technical Patterns
```yaml
tech_patterns:
  - '\b(?:XVID|DIVX|H264|H\.264|H265|H\.265|HEVC|AVC|VP9|X264)\b'
```

#### Language Patterns
Supports both Chinese and English language markers:
- Chinese: 国语, 粤语, 台配, 日语, 韩语, 英语, etc.
- Subtitle markers: 中字, 中英双字, 双语, 字幕
- Version markers: 无水印, 完整版, 高清版, etc.
- English: Filipino, Tagalog, English, Chinese

### 3. MovieFileScanner Class

Main scanner class for processing movie files.

#### Constructor
```python
MovieFileScanner(config: Optional[MovieFileScannerConfig] = None)
```

#### Key Methods

##### scan_directory(directory, recursive=True)
Scans a directory for movie files and extracts information.

**Parameters:**
- `directory` (Path): Directory path to scan
- `recursive` (bool): Whether to scan subdirectories (default: True)

**Returns:**
- `List[MovieFileInfo]`: List of parsed movie file information

**Example:**

```python
from pathlib import Path
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig

# Load configuration
config = MovieFileScannerConfig(Path("configs/movie_file_util.yml"))
scanner = MovieFileScanner(config)

# Scan directory
movies = scanner.scan_directory(Path("/path/to/movies"))
print(f"Found {len(movies)} movies")
```

##### extract_movie_info(file_path)
Extracts movie information from a single file.

**Parameters:**
- `file_path` (Path): Path to the movie file

**Returns:**
- `Optional[MovieFileInfo]`: Parsed movie information or None if parsing fails

## High-Level Function

### scan_movies_from_directory(directory, config_file=None, recursive=True)

Convenience function that combines scanning and configuration loading.

**Parameters:**
- `directory` (str): Directory path to scan
- `config_file` (Optional[str]): Path to configuration file (auto-detected if None)
- `recursive` (bool): Whether to scan subdirectories

**Returns:**
- `List[Dict]`: List of dictionaries containing movie information

**Return Format:**
```json
[
    {
        "file_path": "/full/path/to/movie.mp4",
        "movie_name": "Movie Title",
        "year": "2010",
        "extension": ".mp4",
        "raw_filename": "Movie.Title.2010.1080p.BluRay.mp4"
    }
]
```

**Auto-configuration Detection:**
Looks for configuration files in this order:
1. `{directory_name}.yml`
2. `{directory_name}.yaml`  
3. `config.yml`
4. `config.yaml`

## Usage Examples

### Basic Usage

```python
from utils.movie_file_util import scan_movies_from_directory

# Simple usage with auto-config detection
movies = scan_movies_from_directory("/path/to/movies")

# Process results
for movie in movies:
    print(f"{movie['movie_name']} ({movie['year']}) - {movie['file_path']}")
```

### Advanced Usage with Custom Configuration

```python
from pathlib import Path
from utils.movie_file_util import MovieFileScanner, MovieFileScannerConfig

# Explicit configuration
config_path = Path("configs/movie_file_util.yml")
config = MovieFileScannerConfig(config_path)
scanner = MovieFileScanner(config)

# Scan with custom settings
movies = scanner.scan_directory(Path("/home/user/Videos"), recursive=True)

for movie_info in movies:
    print(f"Title: {movie_info.movie_name}")
    print(f"Year: {movie_info.year or 'Unknown'}")
    print(f"File: {movie_info.file_path}")
    print("---")
```

### Filtering and Processing

```python
from utils.movie_file_util import scan_movies_from_directory

# Get all movies
all_movies = scan_movies_from_directory("/movies")

# Filter by year
recent_movies = [m for m in all_movies if m['year'] and int(m['year']) >= 2020]

# Filter by extension
mkv_movies = [m for m in all_movies if m['extension'] == '.mkv']

# Group by year
from collections import defaultdict

movies_by_year = defaultdict(list)
for movie in all_movies:
    year_key = movie['year'] or 'Unknown'
    movies_by_year[year_key].append(movie)

# Display grouped results
for year, movies in sorted(movies_by_year.items()):
    print(f"\n{year} ({len(movies)} movies):")
    for movie in movies:
        print(f"  - {movie['movie_name']}")
```

## Configuration Details

### Pattern Processing Pipeline

The filename processing follows this pipeline:

1. **Year Extraction**: Identifies potential years using context analysis
2. **Pattern Cleanup**: Applies all configured patterns in a single pass
3. **Separator Normalization**: Converts dots/hyphens/underscores to spaces
4. **Whitespace Cleanup**: Removes extra spaces and trims
5. **Validation**: Ensures meaningful result is produced

### Year Detection Logic

The system uses contextual analysis to identify release years:
- Looks for 4-digit numbers in range 1900-2030
- Analyzes surrounding context for technical indicators
- Scores candidates based on position and context
- Selects the highest-scoring valid year

### Pattern Matching Examples

Given filename: `[阳光电影]Inception.2010.1080p.BluRay.X264.AAC.中英双字.mp4`

Processing steps:
1. Remove `[阳光电影]` (website pattern)
2. Extract year `2010` 
3. Remove `1080p` (resolution pattern)
4. Remove `BluRay` (quality pattern)
5. Remove `X264` (codec pattern)
6. Remove `AAC` (audio pattern)
7. Remove `中英双字` (subtitle pattern)
8. Normalize separators
9. Result: `Inception`

## Error Handling

### Configuration Errors
- Missing configuration file
- Invalid YAML syntax
- Missing required sections

### Processing Errors
- Invalid directory paths
- Permission denied
- File parsing failures
- Empty or invalid filenames

### Logging
All operations are logged with appropriate levels:
- DEBUG: Detailed processing steps
- INFO: Success messages and counts
- WARNING: Non-critical issues
- ERROR: Critical failures

## Performance Characteristics

### Optimizations
- Regex patterns compiled once during configuration loading
- Single-pass pattern matching for efficiency
- Memory-efficient file-by-file processing
- Cached configuration objects

### Performance Tips
- Use specific extensions to reduce scanning scope
- Place frequently matched patterns first
- Avoid overly complex regex patterns
- Consider `recursive=False` for flat structures

## Return Format Specifications

### MovieFileInfo Object
```json
{
    "file_path": "Path object representing full file path",
    "movie_name": "Cleaned movie title string",
    "year": "4-digit year string or null",
    "extension": "File extension including dot",
    "raw_filename": "Original filename with extension"
}
```

### Dictionary Format (scan_movies_from_directory)
```json
{
    "file_path": "/absolute/path/to/file.mp4",
    "movie_name": "Extracted Movie Title",
    "year": "2010",
    "extension": ".mp4", 
    "raw_filename": "Original.Filename.2010.1080p.BluRay.mp4"
}
```

## Common Use Cases

### 1. Media Library Organization
```python
# Scan and organize movies by year
movies = scan_movies_from_directory("/media/library")
organized = {}
for movie in movies:
    year = movie['year'] or 'Unknown'
    if year not in organized:
        organized[year] = []
    organized[year].append(movie)
```

### 2. Duplicate Detection
```python
# Find potential duplicates by movie name
from collections import defaultdict

movies = scan_movies_from_directory("/movies")
name_groups = defaultdict(list)

for movie in movies:
    name_groups[movie['movie_name']].append(movie)

duplicates = {name: files for name, files in name_groups.items() if len(files) > 1}
```

### 3. Quality Analysis
```python
# Analyze movie quality distribution
movies = scan_movies_from_directory("/collection")
qualities = defaultdict(int)

for movie in movies:
    filename = movie['raw_filename'].lower()
    if '1080p' in filename:
        qualities['1080p'] += 1
    elif '720p' in filename:
        qualities['720p'] += 1
    elif '4k' in filename:
        qualities['4K'] += 1
    else:
        qualities['Other'] += 1

print("Quality Distribution:", dict(qualities))
```

## Limitations

1. **Filename Quality Dependent**: Accuracy varies with filename consistency
2. **Year Ambiguity**: Multiple 4-digit numbers may cause incorrect detection
3. **Encoding Issues**: Non-standard encodings may cause parsing problems
4. **Pattern Coverage**: May not handle all release group naming schemes
5. **Context Sensitivity**: Relies on contextual clues for accurate parsing

## Dependencies

- Python 3.7+
- `pathlib`: Path manipulation
- `re`: Regular expressions
- `dataclasses`: Data structure support
- `typing`: Type annotations
- `yaml`: Configuration file parsing
- `logging_util`: Custom logging (internal)

## Configuration File Location

The default configuration file should be located at:
`configs/movie_filename_util.yml`

This path is automatically detected by the convenience functions.