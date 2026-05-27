# Douban API URL Documentation

## Overview
This document summarizes all Douban-related URLs used in the project and their parameters.

## Main Search URL

### Search by Movie Name and Year
```commandline
https://www.douban.com/search?cat=1002&q={movie_name} {year}
```

**Parameters:**
- `cat=1002`: Specifies movie category search
- `q={movie_name} {year}`: Search query combining movie name and year

**Useful Return Information:**
- HTML search results containing movie entries
- Each result includes:
  - Movie title with `[电影]` marker
  - Rating information (stars and numerical score)
  - Review count (number of ratings)
  - Original title (foreign language names)
  - Subject-cast information (directors, actors, year)
  - Brief description/plot summary
  - Douban movie ID (sid) for detailed queries

**Example Response Structure:**
```html
<div class="result">
  <div class="title">
    <h3><span>[电影]</span>&nbsp;<a>Movie Title</a></h3>
  </div>
  <div class="rating-info">
    <span class="rating_nums">8.7</span>
    <span>(12345人评价)</span>
    <span class="subject-cast">原名:Original Title / Director / Actor1 / Actor2 / 2024</span>
  </div>
  <p>Brief movie description...</p>
</div>
```

## Movie Details URL

### Get Detailed Movie Information
```commandline
https://movie.douban.com/subject/{sid}/
```

**Parameters:**
- `{sid}`: Douban movie ID extracted from search results

**Useful Return Information:**
- Complete movie details page
- Detailed rating and review statistics
- Full cast and crew information
- Extended plot description
- Genre classification
- Release dates and box office information
- User reviews and discussions

## Verification Handling URLs

### Anti-bot Verification Process
The system automatically handles Douban's anti-bot verification through:

1. **Initial Request**: Direct access to target URL
2. **Verification Detection**: System detects redirect to verification page
3. **POW Calculation**: Automatic Proof of Work computation
4. **Verification Submission**: Submit computed proof to bypass verification

**Referer URLs used in verification:**
- `https://www.douban.com/`: Main site referer
- Target movie URLs for detailed pages

## Additional Resource URLs

### Static Resources
- CSS and JavaScript files from `https://img1.doubanio.com/`
- Image assets for movie posters and UI elements

### Mobile App Redirects
- iOS app download: `https://www.douban.com/doubanapp/redirect?channel=top-nav&direct_dl=1&download=iOS`
- Android app download: `https://www.douban.com/doubanapp/redirect?channel=top-nav&direct_dl=1&download=Android`

## Navigation URLs

### Site Sections
- Main site: `https://www.douban.com`
- Movies section: `https://movie.douban.com`
- Books section: `https://book.douban.com`
- Music section: `https://music.douban.com`

## Error Handling and Edge Cases

### Common Response Patterns
- Empty search results when no movies found
- Multiple results requiring filtering by year
- Mixed content (movies, TV shows, documentaries)
- Rate limiting and temporary blocks

### Data Extraction Points
- `sid` values for detailed queries
- Rating scores and review counts
- Original foreign titles
- Cast information parsing
- Year validation and extraction