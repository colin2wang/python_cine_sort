# Change History

This document records all significant changes to the Music Library Organizer project, organized by date in reverse chronological order.

---

## Update Rules

### Documentation Guidelines
- Each daily entry must not exceed 200 words
- Use concise English descriptions focusing on key changes
- List modified files when relevant
- Highlight new features, bug fixes, and improvements separately
- Maintain reverse chronological order (newest first)
- Use clear section headers with dates
- Avoid redundant details; focus on impact and functionality
- Group related changes under unified headings
- Preserve technical accuracy while ensuring readability

---

## 2026-05-27

### Douban Result Documentation Enhancement
- Moved Douban search result HTML to markdown documentation (`docs/douban_search_result.md`)
- Moved Douban details result HTML to markdown documentation (`docs/douban_details_result.md`)
- Updated test files to reference new markdown file paths
- Improved test data organization for better maintainability

### Project Documentation Setup
- Added CHANGE_HISTORY.md for tracking project changes
- Added PROXYAI.md for AI assistant proxy configuration documentation
- Updated README.md with current project structure and documentation links
- Modified process_with_folder.py script with latest improvements

---

## 2024-04-18

### Initial Documentation Setup
- Documented change history format and documentation guidelines
- Established structure for future entries with date headers
- Defined rules for daily entry content (max 200 words)
- Added formatting requirements for consistency

---

## 2026-04-25

### Logger Utility Overhaul
- Removed deprecated `logging_util.py` (253 lines)
- Added new `logging_config.py` with comprehensive logging configuration (128 lines)
- Updated `.gitignore` with new file patterns
- Modified test files to work with new logging utilities

## 2026-04-24

### Movie Organization Utility Release
- Added movie organization utility module (`utils/movie_org_util.py`)
- Created configuration file `configs/movie_org_util.yml`
- Implemented comprehensive testing framework for movie organization features
- Added tests for full process workflow

---

## 2026-02-21

### README and File Utility Refactoring
- Updated README.md with additional tools documentation (+10 lines)
- Renamed `movie_filename_util.yml` to `movie_file_util.yml`
- Enhanced movie file utility module (`utils/movie_sort_util.py`)
- Added test suite for movie sort utilities

## 2026-02-20

### API Documentation Expansion
- Added comprehensive Douban details API documentation (`docs/douban_details.md`, 242 lines)
- Created Douban search API documentation (`docs/douban_search.md`, 196 lines)
- Added movie filename utility documentation (`docs/movie_filename_util.md`, 380 lines)
- Enhanced test data for Douban details

### README Documentation Overhaul
- Major README update with expanded documentation (+399 lines, -100 deletions)

---

## 2026-02-19

### Movie Filename Logic Improvements
- Rewrote movie filename logic with improved parsing algorithms (-665 lines)
- Updated configuration files to match new patterns (+278 lines)
- Enhanced test coverage for filename utilities

### Douban Integration Refactor
- Split and reorganized Douban utility functions
- Improved error handling and response processing
- Added comprehensive URL documentation (`douban_query_url.md`)

---

## 2026-02-18

### Details Page API Implementation
- Added details page API endpoint in `utils/douban_details.py`
- Created search utility module (`utils/douban_search.py`)
- Enhanced movie file parsing capabilities
- Improved logging utilities with better configuration

### Project Initialization
- Initial project structure creation
- Implemented core movie file utility functions
- Set up Douban HTML parsing utilities
- Added comprehensive test framework and data files

---