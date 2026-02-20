# Douban Details Documentation

## Overview

The `DoubanDetailsParser` class is designed to parse detailed movie information from Douban movie detail pages. It extracts comprehensive metadata including basic information, ratings, cast details, plot summaries, and technical specifications from HTML content.

## Class Definition

```python
class DoubanDetailsParser:
    """Parser for extracting detailed movie information from Douban movie pages."""
```

## Methods

### `__init__(self, html_content: str)`

Initialize the parser with HTML content from a Douban movie detail page.

**Parameters:**
- `html_content` (str): Raw HTML content of the Douban movie detail page

**Example:**
```python
parser = DoubanDetailsParser(html_content)
```

### `parse_basic_info(self) -> dict`

Parse basic movie information including title, year, director, actors, genre, region, language, and duration.

**Returns:**
```python
{
    "title": str,           # Movie title (Chinese)
    "original_title": str,  # Original title (if different)
    "year": int,            # Release year
    "director": str,        # Director name
    "actors": [str],        # List of main actors
    "genre": [str],         # List of genres
    "region": str,          # Production region/country
    "language": str,        # Primary language
    "duration": str         # Movie duration (e.g., "120分钟")
}
```

### `parse_rating_info(self) -> dict`

Parse rating information including average score, rating count, and rating distribution.

**Returns:**
```python
{
    "rating": float,        # Average rating (0-10 scale)
    "rating_count": int,    # Number of ratings
    "rating_distribution": {
        "5_star": int,      # Count of 5-star ratings
        "4_star": int,      # Count of 4-star ratings
        "3_star": int,      # Count of 3-star ratings
        "2_star": int,      # Count of 2-star ratings
        "1_star": int       # Count of 1-star ratings
    }
}
```

### `parse_cast_details(self) -> dict`

Parse detailed cast information including directors and main actors with their roles.

**Returns:**
```python
{
    "directors": [
        {
            "name": str,        # Director name
            "role": str         # Role description
        }
    ],
    "actors": [
        {
            "name": str,        # Actor name
            "character": str,   # Character played
            "role": str         # Role description
        }
    ]
}
```

### `parse_plot_summary(self) -> dict`

Parse plot summary and storyline information.

**Returns:**
```python
{
    "summary": str,         # Main plot summary
    "storyline": str        # Detailed storyline description
}
```

### `parse_technical_info(self) -> dict`

Parse technical specifications including IMDb ID, release dates, and production details.

**Returns:**
```python
{
    "imdb_id": str,         # IMDb identifier
    "release_date": str,    # Release date
    "episode_count": int,   # Episode count (for series)
    "runtime": str,         # Runtime per episode/movie
    "official_website": str,# Official website URL
    "production_company": [str] # Production companies
}
```

### `parse_all_info(self) -> dict`

Parse all available information and return a comprehensive movie data structure.

**Returns:**
```python
{
    "basic_info": {
        # Same structure as parse_basic_info()
    },
    "rating_info": {
        # Same structure as parse_rating_info()
    },
    "cast_details": {
        # Same structure as parse_cast_details()
    },
    "plot_summary": {
        # Same structure as parse_plot_summary()
    },
    "technical_info": {
        # Same structure as parse_technical_info()
    }
}
```

## Usage Examples

### Basic Usage

```python
from utils.douban_details import DoubanDetailsParser

# Load HTML content (typically from a Douban movie detail page)
with open('movie_detail_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Create parser instance
parser = DoubanDetailsParser(html_content)

# Parse all information
movie_data = parser.parse_all_info()

print(f"Title: {movie_data['basic_info']['title']}")
print(f"Rating: {movie_data['rating_info']['rating']}/10")
print(f"Director: {movie_data['basic_info']['director']}")
```

### Selective Parsing

```python
# Parse only specific information
basic_info = parser.parse_basic_info()
rating_info = parser.parse_rating_info()

print(f"Movie: {basic_info['title']} ({basic_info['year']})")
print(f"Average Rating: {rating_info['rating']} from {rating_info['rating_count']} votes")
```

### Accessing Cast Information

```python
cast_details = parser.parse_cast_details()

# Display director information
for director in cast_details['directors']:
    print(f"Director: {director['name']}")

# Display main actors
print("Main Cast:")
for actor in cast_details['actors'][:5]:  # First 5 actors
    print(f"- {actor['name']} as {actor['character']}")
```

## Error Handling

The parser includes robust error handling for various scenarios:

- **Missing Elements**: Returns appropriate default values when HTML elements are not found
- **Parsing Errors**: Gracefully handles malformed HTML or unexpected data formats
- **Network Issues**: Designed to work with pre-fetched HTML content, avoiding direct network dependencies

## Data Validation

The parser performs validation on extracted data:

- **Type Checking**: Ensures data types match expected formats
- **Range Validation**: Validates numerical values (ratings between 0-10, years in reasonable range)
- **Data Cleaning**: Removes extra whitespace and normalizes text formatting

## Performance Considerations

- **Single Pass Parsing**: Efficiently parses HTML content in a single traversal
- **Memory Efficient**: Processes HTML without loading entire DOM tree into memory
- **Caching**: Internal caching of parsed elements for repeated access

## Dependencies

- `BeautifulSoup4`: For HTML parsing and navigation
- `requests`: For fetching HTML content (if needed)
- Standard Python libraries: `re`, `json`, `urllib`

## Integration with Other Components

This parser works seamlessly with other components in the movie sorting system:

- **DoubanSearch**: Provides search functionality to find movie IDs
- **MovieFilenameUtil**: Uses parsed information for filename generation
- **CommonUtil**: Leverages shared utility functions for data processing

## Best Practices

1. **Input Validation**: Always validate HTML content before parsing
2. **Error Handling**: Implement proper exception handling in production code
3. **Data Verification**: Cross-reference parsed data with multiple sources when accuracy is critical
4. **Performance**: Cache parsed results when processing multiple movies

## Version Information

- **Current Version**: 1.0
- **Last Updated**: [Current Date]
- **Python Version**: 3.7+

## See Also

- [Douban Search Documentation](douban_search.md)
- [Movie Filename Utility Documentation](movie_filename_util.md)