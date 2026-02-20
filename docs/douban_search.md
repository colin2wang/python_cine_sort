# Douban Search Documentation

This document describes the usage and return formats of the Douban movie search functionality in `douban_search.py`.

## Overview

The module provides functions to search for movies on Douban and parse the search results to extract structured movie information.

## Functions

### 1. get_movie_search_result_html(name, year)

Retrieves the HTML content of Douban movie search results.

#### Parameters
- `name` (str): Movie name/title to search for
- `year` (str): Release year of the movie (optional)

#### Returns
- `Optional[str]`: HTML response content from Douban search page, or `None` if request fails

#### Example Usage
```python
from utils.douban_search import get_movie_search_result_html

# Search with both name and year
html_content = get_movie_search_result_html("Inception", "2010")

# Search with name only
html_content = get_movie_search_result_html("The Matrix", "")
```

#### Error Handling
The function handles various exceptions:
- `requests.exceptions.Timeout`: Request timeout
- `requests.exceptions.ConnectionError`: Network connection issues
- `requests.exceptions.HTTPError`: HTTP status errors
- `requests.exceptions.RequestException`: Other request-related errors
- General `Exception`: Unexpected errors

### 2. parse_movie_search_result(html_content)

Parses movie information from Douban search results HTML content.

#### Parameters
- `html_content` (str): HTML content from Douban search results

#### Returns
- `dict`: Structured movie information dictionary

#### Return Format
The function returns a dictionary with the following structure:

```json
{
    "title": "Movie Title",
    "rating": "8.8",

    "directors": ["Director Name"],
    "actors": ["Actor 1", "Actor 2", "Actor 3"],
    "year": "2010",
    "genres": [],
    "original_title": "Original Movie Title",
    "review_count": "100000",
    "sid": "1234567",
    "error": null
}
```

#### Field Descriptions
| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Chinese movie title |
| `rating` | string | Movie rating score (e.g., "8.8") |
| `directors` | list | List of director names |
| `actors` | list | List of main actor names (max 5) |
| `year` | string | Release year |
| `genres` | list | Movie genres (currently empty) |
| `original_title` | string | Original/foreign movie title |
| `review_count` | string | Number of user reviews |
| `sid` | string | Douban movie ID |
| `error` | string/null | Error message if parsing failed |

#### Example Usage
```python
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result

# Get HTML content
html_content = get_movie_search_result_html("Inception", "2010")

if html_content:
    # Parse movie information
    movie_info = parse_movie_search_result(html_content)
    
    print(f"Title: {movie_info['title']}")
    print(f"Rating: {movie_info['rating']}")
    print(f"Directors: {', '.join(movie_info['directors'])}")
    print(f"Actors: {', '.join(movie_info['actors'])}")
    print(f"Year: {movie_info['year']}")
```

## Error Handling

Both functions include comprehensive error handling:

### get_movie_search_result_html Errors
- Returns `None` on any request failure
- Logs appropriate warning/error messages
- Includes random delay between requests to avoid rate limiting

### parse_movie_search_result Errors
- Returns empty movie info dictionary with error message on parsing failures
- Handles `None` or invalid HTML content gracefully
- Uses fallback parsing methods when primary parsing fails

## Usage Examples

### Basic Movie Search
```python
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result

def search_movie(title, year=None):
    """Complete movie search workflow"""
    # Step 1: Get search results
    html_content = get_movie_search_result_html(title, year or "")
    
    if not html_content:
        return {"error": "Failed to retrieve search results"}
    
    # Step 2: Parse movie information
    movie_info = parse_movie_search_result(html_content)
    
    return movie_info

# Example usage
result = search_movie("The Shawshank Redemption", "1994")
if not result.get('error'):
    print(f"Found: {result['title']} ({result['year']})")
    print(f"Rating: {result['rating']}/10")
else:
    print(f"Error: {result['error']}")
```

### Batch Processing
```python
from utils.douban_search import get_movie_search_result_html, parse_movie_search_result

movies = [
    {"title": "Inception", "year": "2010"},
    {"title": "Interstellar", "year": "2014"},
    {"title": "Dunkirk", "year": "2017"}
]

results = []
for movie in movies:
    html_content = get_movie_search_result_html(movie["title"], movie["year"])
    if html_content:
        movie_info = parse_movie_search_result(html_content)
        results.append({
            "search_term": f"{movie['title']} ({movie['year']})",
            "result": movie_info
        })
```

## Technical Details

### HTTP Headers
The module uses realistic browser headers to avoid detection:
- User-Agent simulating Chrome browser
- Accept headers for HTML content
- Language preferences set to Chinese/English

### Parsing Strategy
The parser uses regex-based extraction with multiple fallback mechanisms:
1. Primary parsing of structured result blocks
2. Fallback to loose title matching when structured parsing fails
3. Content filtering to exclude non-movie results

### Rate Limiting
Includes random delays between requests to respect Douban's rate limits and avoid IP blocking.

## Notes and Limitations

1. **Accuracy**: Results depend on Douban's search algorithm and may vary
2. **Rate Limits**: Heavy usage may trigger anti-bot measures
3. **Data Completeness**: Some fields may be empty depending on available information
4. **Language**: Currently optimized for Chinese movie titles and content
5. **Structure Changes**: May require updates if Douban changes their HTML structure

## Dependencies

- `requests`: For HTTP requests
- `re`: For regex parsing
- Custom utilities from `utils` package:
  - `get_default_logger()`: Logging functionality
  - `sleep_for_random_time()`: Random delay implementation