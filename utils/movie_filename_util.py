"""Movie file scanning utility module

Used to scan video files in specified directories and extract movie names and year information

filename: movie_filename_util.py
"""

import re
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .logging_util import get_default_logger

logger = get_default_logger()


@dataclass
class MovieFileInfo:
    """Movie file information data class"""
    file_path: Path
    movie_name: str
    year: Optional[str]
    extension: str
    raw_filename: str


class MovieFileScannerConfig:
    """Movie file scanner configuration class"""
    
    def __init__(self, config_file: Optional[Path] = None):
        # Set default values to empty, force reading from configuration file
        self.extensions = []
        self.cleanup_rules = []
        self.year_patterns = []
        self.movie_name_rules = []
        # New configuration items for unified processing
        self.technical_identifiers = []
        self.language_identifiers = []
        self.final_tech_patterns = []
        self.tech_indicators = []
        self.subtitle_keywords = []
        self.common_subtitle_indicators = []

            
        if config_file and config_file.exists():
            self.load_config(config_file)
        else:
            raise ValueError("Must provide valid configuration file path")
    
    def load_config(self, config_file: Path):
        """Load configuration from YAML configuration file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'extensions' in config:
                self.extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                                 for ext in config['extensions']]
                    
            # New cleanup rules configuration
            if 'cleanup_rules' in config:
                self.cleanup_rules = config['cleanup_rules']

                    
            if 'year_patterns' in config:
                self.year_patterns = config['year_patterns']
                    
            # New movie name rules configuration
            if 'movie_name_rules' in config:
                self.movie_name_rules = config['movie_name_rules']
                
            # Load unified processing configuration items
            if 'technical_identifiers' in config:
                self.technical_identifiers = config['technical_identifiers']
                
            if 'language_identifiers' in config:
                self.language_identifiers = config['language_identifiers']
                
            if 'final_tech_patterns' in config:
                self.final_tech_patterns = config['final_tech_patterns']
                
            if 'tech_indicators' in config:
                self.tech_indicators = config['tech_indicators']
                
            if 'subtitle_keywords' in config:
                self.subtitle_keywords = config['subtitle_keywords']
                
            if 'common_subtitle_indicators' in config:
                self.common_subtitle_indicators = config['common_subtitle_indicators']
                
            logger.debug(f"✓ Configuration loaded from {config_file}")
            
        except Exception as e:
            logger.warning(f"✗ Failed to load configuration file: {e}, using default configuration")


class MovieFileScanner:
    """Movie file scanner"""
    
    def __init__(self, config: Optional[MovieFileScannerConfig] = None):
        self.config = config or MovieFileScannerConfig()
        self.logger = get_default_logger()
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[MovieFileInfo]:
        """Scan movie files in directory
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            List[MovieFileInfo]: List of movie file information
        """
        if not directory.exists():
            self.logger.error(f"✗ Directory does not exist: {directory}")
            return []
        
        if not directory.is_dir():
            self.logger.error(f"✗ Path is not a directory: {directory}")
            return []
        
        movie_files = []
        
        # Determine scan mode
        if recursive:
            file_iterator = directory.rglob('*')
        else:
            file_iterator = directory.iterdir()
        
        for file_path in file_iterator:
            if file_path.is_file() and file_path.suffix.lower() in self.config.extensions:
                movie_info = self.extract_movie_info(file_path)
                if movie_info:
                    movie_files.append(movie_info)
        
        self.logger.info(f"✓ Scan completed, found {len(movie_files)} movie files")
        return movie_files
    
    def extract_movie_info(self, file_path: Path) -> Optional[MovieFileInfo]:
        """Extract movie information from filename
        
        Args:
            file_path: File path
            
        Returns:
            MovieFileInfo: Movie information object, returns None on parsing failure
        """
        try:
            filename = file_path.stem  # Get filename without extension
            extension = file_path.suffix.lower()
            
            # Phase 1: Extract year from original filename (modified to extract from original filename)
            year = self._extract_year_from_original(filename)
            
            # Phase 2 & 3: Process filename and extract movie name in one step
            cleaned_name, movie_name = self._process_movie_name(filename)
            
            if not cleaned_name:
                self.logger.warning(f"✗ Cleaned filename is empty: {file_path.name}")
                return None
            
            if not movie_name:
                self.logger.warning(f"✗ Cannot extract movie name from cleaned filename: {file_path.name} -> {cleaned_name}")
                return None
            
            movie_info = MovieFileInfo(
                file_path=file_path,
                movie_name=movie_name,
                year=year,
                extension=extension,
                raw_filename=file_path.name
            )
            
            self.logger.debug(f"✓ Parsed file: {file_path.name} -> Original year: {year}, Cleaned: {cleaned_name}, Name: {movie_name}")
            return movie_info
            
        except Exception as e:
            self.logger.error(f"✗ Error parsing file {file_path.name}: {e}")
            return None
    
    def _process_movie_name(self, filename: str) -> Tuple[str, str]:
        """Unified method to process filename and extract clean movie name
        
        This method combines the functionality of _cleanup_filename and 
        _extract_movie_name_from_cleaned to eliminate duplicate logic.
        All parameters are moved to configuration file.
        
        Args:
            filename: Original filename
            
        Returns:
            Tuple[str, str]: (cleaned_filename, final_movie_name)
        """
        original = filename
        processed = filename
        
        # Phase 1: Handle subtitle segments
        subtitle_segments = self._extract_subtitle_segments(processed)
        for segment in subtitle_segments:
            processed = processed.replace(segment, ' ')
            self.logger.debug(f"Remove subtitle segment: '{segment}'")
        
        # Phase 2: Apply configuration cleanup rules
        for i, pattern in enumerate(self.config.cleanup_rules, 1):
            before_clean = processed
            processed = re.sub(pattern, ' ', processed)
            if before_clean != processed:
                self.logger.debug(f"Cleanup rule {i} applied: '{pattern}' -> '{before_clean}' => '{processed}'")
        
        # Phase 3: Convert separators to spaces
        processed = re.sub(r'[.\-_]+', ' ', processed)
        processed = re.sub(r'\s+', ' ', processed)
        processed = processed.strip()
        
        # Store intermediate cleaned result
        cleaned_filename = processed
        
        # Phase 4: Apply movie name extraction rules
        for i, pattern in enumerate(self.config.movie_name_rules, 1):
            match = re.search(pattern, cleaned_filename, re.IGNORECASE)
            if match:
                movie_name = match.group(1).strip()
                if movie_name:
                    self.logger.debug(f"Movie name rule {i} matched successfully: '{cleaned_filename}' -> '{movie_name}'")
                    return cleaned_filename, movie_name
        
        # Phase 5: Fine-tune processing for residual technical information
        refined_name = cleaned_filename
        
        # Remove residual years (stricter matching)
        refined_name = re.sub(r'(?:^|\s)(19|20)\d{2}(?:$|\s)', ' ', refined_name)
        
        # Remove technical identifiers using configuration
        for pattern in self.config.technical_identifiers:
            refined_name = re.sub(pattern, ' ', refined_name, flags=re.IGNORECASE)
        
        # Remove language and subtitle identifiers using configuration
        for pattern in self.config.language_identifiers:
            refined_name = re.sub(pattern, ' ', refined_name, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        refined_name = re.sub(r'\s+', ' ', refined_name)  # Merge multiple spaces
        refined_name = re.sub(r'[\s\-_.]+$', '', refined_name)  # Remove trailing spaces and punctuation
        refined_name = re.sub(r'^[\s\-_.]+', '', refined_name)  # Remove leading spaces and punctuation
        refined_name = refined_name.strip()
        
        # Remove residual technical identifiers (final fine-tuning)
        # Handle year removal separately
        refined_name = re.sub(r'(?:^|\s)(19|20)\d{2}(?:$|\s)', ' ', refined_name)
        
        for pattern in self.config.final_tech_patterns:
            refined_name = re.sub(pattern, ' ', refined_name, flags=re.IGNORECASE)
            refined_name = re.sub(r'\s+', ' ', refined_name)  # Re-merge spaces
        
        refined_name = refined_name.strip()
        
        # Remove isolated single characters
        words = refined_name.split()
        filtered_words = [word for word in words if len(word) > 1 or word.isalnum()]
        final_movie_name = ' '.join(filtered_words)
        
        if final_movie_name:
            self.logger.debug(f"Fine-tuned processing: '{cleaned_filename}' -> '{final_movie_name}'")
        else:
            # Final fallback
            final_movie_name = cleaned_filename
            self.logger.debug(f"Using default rule: '{cleaned_filename}' -> '{final_movie_name}'")
        
        self.logger.debug(f"Filename processing completed: '{original}' -> Cleaned: '{cleaned_filename}', Movie name: '{final_movie_name}'")
        return cleaned_filename, final_movie_name
    
    def _cleanup_filename(self, filename: str) -> str:
        """Clean up useless information in filename
        
        DEPRECATED: This method is kept for backward compatibility.
        Use _process_movie_name() instead.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Cleaned filename
        """
        cleaned_filename, _ = self._process_movie_name(filename)
        return cleaned_filename
    
    def _extract_movie_name_from_cleaned(self, cleaned_filename: str) -> str:
        """Extract movie name from cleaned filename
        
        DEPRECATED: This method is kept for backward compatibility.
        Use _process_movie_name() instead.
        
        Args:
            cleaned_filename: Cleaned filename
            
        Returns:
            str: Movie name
        """
        _, movie_name = self._process_movie_name(cleaned_filename)
        return movie_name
    
    def _extract_subtitle_segments(self, filename: str) -> List[str]:
        """Extract complete segments containing subtitle keywords
        
        Args:
            filename: Original filename
            
        Returns:
            List[str]: List of segments to remove
        """
        segments_to_remove = []
        
        # Use subtitle keywords from configuration
        subtitle_keywords = self.config.subtitle_keywords
        
        # Split filename by separators
        parts = re.split(r'[.\-_]+', filename)
        
        for i, part in enumerate(parts):
            # Check if current part contains any subtitle keywords
            contains_subtitle_keyword = False
            matched_keyword = None
            
            for keyword in subtitle_keywords:
                if keyword in part:
                    contains_subtitle_keyword = True
                    matched_keyword = keyword
                    break
            
            # If contains subtitle keyword, determine if it's an independent segment
            if contains_subtitle_keyword:
                # Determine if it's an independent subtitle segment (not part of movie name)
                if self._is_subtitle_segment(part, matched_keyword, parts, i):
                    segments_to_remove.append(part)
                    self.logger.debug(f"Identified subtitle segment: '{part}' (matched keyword: {matched_keyword})")
        
        return segments_to_remove
    
    def _is_subtitle_segment(self, segment: str, keyword: str, all_parts: List[str], index: int) -> bool:
        """Determine if given segment is subtitle-related rather than part of movie name
        
        Args:
            segment: Segment to check
            keyword: Matched keyword
            all_parts: All split segments
            index: Index of current segment in list
            
        Returns:
            bool: True means it's a subtitle segment, False means it might be part of movie name
        """
        # If segment equals keyword itself, it's likely a subtitle identifier
        if segment == keyword:
            return True
        
        # If segment mainly consists of technical identifiers + subtitle keywords combination
        tech_indicators = self.config.tech_indicators
        
        has_tech_indicator = any(indicator in segment.upper() for indicator in tech_indicators)
        
        if has_tech_indicator and keyword in segment:
            return True
        
        # If segment contains combinations of multiple subtitle keywords
        subtitle_keywords = self.config.subtitle_keywords
        
        keyword_count = sum(1 for k in subtitle_keywords if k in segment)
        if keyword_count >= 2:  # Contains multiple subtitle keywords
            return True
        
        # If segment is in the latter half of filename (usually technical information area)
        if index >= len(all_parts) // 2 and len(all_parts) > 3:
            # Check if there are obvious years or technical identifiers before/after
            nearby_parts = all_parts[max(0, index-2):min(len(all_parts), index+3)]
            has_year_or_tech = any(
                re.search(r'(?:19|20)\d{2}', p) or 
                any(indicator in p.upper() for indicator in tech_indicators)
                for p in nearby_parts
            )
            if has_year_or_tech:
                return True
        
        # If keyword is a common subtitle identifier and segment is longer, it might be a combination identifier
        common_subtitle_indicators = self.config.common_subtitle_indicators
        
        if keyword in common_subtitle_indicators and len(segment) > len(keyword):
            return True
        
        # By default, conservatively judge it's not a subtitle segment (avoid accidental deletion)
        return False
    
    def _extract_year_from_original(self, original_filename: str) -> Optional[str]:
        """Extract year from original filename
        
        Args:
            original_filename: Original filename
            
        Returns:
            str: Year string, returns None if not found
        """
        # Use stricter year matching rules
        # Only match standalone 4-digit years (with boundaries)
        year_pattern = r'(?:^|\s|\.)(19|20)\d{2}(?:$|\s|\.)'
        
        # Find all possible years
        matches = list(re.finditer(year_pattern, original_filename))
        valid_years = []
        
        for match in matches:
            year_str = match.group().strip('. ')
            year_num = int(year_str)
            
            # Validate year reasonableness (within 1900-2030 range)
            if 1900 <= year_num <= 2030:
                # Check if it might be part of movie title rather than actual year
                context_before = original_filename[:match.start()].strip()
                context_after = original_filename[match.end():].strip()
                
                # If there's content before and after the year, and lengths aren't too short, it might be part of title
                if len(context_before) > 2 and len(context_after) > 2:
                    # Further check: if year appears in middle of title, it might be plot element rather than release year
                    words_before = context_before.split('.')
                    words_after = context_after.split('.')
                    
                    # For movie filenames, if year is followed by obvious technical identifiers, it's more likely release year
                    # rather than title content
                    if (words_before and len(words_before[-1]) > 1 and 
                        words_after and len(words_after[0]) > 1):
                        # Check if there are technical identifiers after the year
                        next_word = words_after[0].upper()
                        tech_indicators = self.config.tech_indicators
                                                            
                        if any(indicator in next_word for indicator in tech_indicators):
                            # Year followed by technical identifiers, likely release year
                            self.logger.debug(f"Year {year_str} followed by technical identifier '{next_word}', judged as release year")
                            valid_years.append((year_str, match.start()))  # Store year and position
                        else:
                            self.logger.debug(f"Skipping year {year_str}, judged as title content: '{original_filename}'")
                            continue
                    else:
                        # If context is short, it might be release year
                        valid_years.append((year_str, match.start()))
                else:
                    # Years at boundary positions are more likely release years
                    valid_years.append((year_str, match.start()))
                
                self.logger.debug(f"Found valid year: '{original_filename}' -> {year_str}")
        
        # Return the most suitable year:
        # 1. Prefer years closer to technical identifiers
        # 2. If multiple candidates, choose the later positioned one (usually at filename end)
        if valid_years:
            # Sort by position, choose the latest year
            valid_years.sort(key=lambda x: x[1], reverse=True)
            selected_year = valid_years[0][0]
            self.logger.debug(f"Selected year: {selected_year} (position: {valid_years[0][1]})")
            return selected_year
        
        return None
    



def scan_movies_from_directory(directory: str, 
                              config_file: Optional[str] = None,
                              recursive: bool = True) -> List[Dict]:
    """Convenience function: scan directory and return results in dictionary format
    
    Args:
        directory: Directory path
        config_file: Configuration file path (optional)
        recursive: Whether to scan recursively
        
    Returns:
        List[Dict]: Dictionary list containing movie information
    """
    dir_path = Path(directory)
    
    # Find same-name configuration files
    if config_file is None:
        config_candidates = [
            dir_path / f"{dir_path.name}.yml",
            dir_path / f"{dir_path.name}.yaml",
            dir_path / "config.yml",
            dir_path / "config.yaml"
        ]
        for candidate in config_candidates:
            if candidate.exists():
                config_file = str(candidate)
                break
    
    # Create configuration object
    config_obj = None
    if config_file:
        config_obj = MovieFileScannerConfig(Path(config_file))
    
    # Scan files
    scanner = MovieFileScanner(config_obj)
    movie_files = scanner.scan_directory(dir_path, recursive)
    
    # Convert to dictionary format
    result = []
    for movie_info in movie_files:
        result.append({
            'file_path': str(movie_info.file_path),
            'movie_name': movie_info.movie_name,
            'year': movie_info.year,
            'extension': movie_info.extension,
            'raw_filename': movie_info.raw_filename
        })
    
    return result