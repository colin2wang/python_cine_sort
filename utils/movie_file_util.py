"""Movie file scanning utility module

Used to scan video files in specified directories and extract movie names and year information

filename: movie_file_util.py
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Set

import yaml

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
        # Core configuration
        self.extensions: List[str] = []
        self.year_pattern: str = r'(?:19|20)\d{2}'

        # Processing patterns (unified)
        self.cleanup_patterns: List[str] = []
        self.tech_patterns: List[str] = []
        self.language_patterns: List[str] = []

        if config_file and config_file.exists():
            self.load_config(config_file)
        else:
            raise ValueError("Must provide valid configuration file path")

    def load_config(self, config_file: Path):
        """Load configuration from YAML configuration file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Load extensions
            if 'extensions' in config:
                self.extensions = [
                    ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                    for ext in config['extensions']
                ]

            # Load unified patterns
            self.cleanup_patterns = config.get('cleanup_patterns', [])
            self.tech_patterns = config.get('tech_patterns', [])
            self.language_patterns = config.get('language_patterns', [])

            # Compile combined regex for performance
            self._compile_patterns()

            logger.debug(f"✓ Configuration loaded from {config_file}")

        except Exception as e:
            logger.error(f"✗ Failed to load configuration file: {e}")
            raise

    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        # Combine all removal patterns into one for efficiency
        all_patterns = (
            self.cleanup_patterns +
            self.tech_patterns +
            self.language_patterns
        )

        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_patterns = []
        for p in all_patterns:
            if p not in seen:
                seen.add(p)
                unique_patterns.append(p)

        # Create master pattern for cleanup phase
        if unique_patterns:
            self._master_cleanup_regex = re.compile(
                '|'.join(f'({p})' for p in unique_patterns),
                re.IGNORECASE
            )
        else:
            self._master_cleanup_regex = None

        # Compile year pattern
        self._year_regex = re.compile(self.year_pattern)


class MovieFileScanner:
    """Movie file scanner"""

    def __init__(self, config: Optional[MovieFileScannerConfig] = None):
        self.config = config or MovieFileScannerConfig()
        self.logger = get_default_logger()

    def scan_directory(self, directory: Path, recursive: bool = True) -> List[MovieFileInfo]:
        """Scan movie files in directory"""
        if not directory.exists():
            self.logger.error(f"✗ Directory does not exist: {directory}")
            return []

        if not directory.is_dir():
            self.logger.error(f"✗ Path is not a directory: {directory}")
            return []

        movie_files = []
        file_iterator = directory.rglob('*') if recursive else directory.iterdir()

        for file_path in file_iterator:
            if file_path.is_file() and file_path.suffix.lower() in self.config.extensions:
                movie_info = self.extract_movie_info(file_path)
                if movie_info:
                    movie_files.append(movie_info)

        self.logger.info(f"✓ Scan completed, found {len(movie_files)} movie files")
        return movie_files

    def extract_movie_info(self, file_path: Path) -> Optional[MovieFileInfo]:
        """Extract movie information from filename"""
        try:
            filename = file_path.stem
            extension = file_path.suffix.lower()

            # Extract year first (from original filename)
            year = self._extract_year(filename)

            # Process filename to get movie name
            movie_name = self._process_movie_name(filename)

            if not movie_name:
                self.logger.warning(f"✗ Cannot extract movie name: {file_path.name}")
                return None

            movie_info = MovieFileInfo(
                file_path=file_path,
                movie_name=movie_name,
                year=year,
                extension=extension,
                raw_filename=file_path.name
            )

            self.logger.debug(
                f"✓ Parsed: {file_path.name} -> Year: {year}, Name: {movie_name}"
            )
            return movie_info

        except Exception as e:
            self.logger.error(f"✗ Error parsing file {file_path.name}: {e}")
            return None

    def _process_movie_name(self, filename: str) -> str:
        """
        Unified method to process filename and extract clean movie name.

        Single-pass processing pipeline:
        1. Apply all cleanup patterns (brackets, websites, tech specs, etc.)
        2. Normalize separators
        3. Clean up residual artifacts
        4. Validate result
        """
        original = filename
        processed = filename

        # Step 1: Apply all cleanup patterns in single pass
        if self.config._master_cleanup_regex:
            before = processed
            processed = self.config._master_cleanup_regex.sub(' ', processed)
            if before != processed:
                self.logger.debug(f"After pattern cleanup: '{before}' -> '{processed}'")

        # Step 2: Normalize separators and whitespace
        # Replace dots, hyphens, underscores with spaces
        processed = re.sub(r'[.\-_]+', ' ', processed)
        # Collapse multiple spaces
        processed = re.sub(r'\s+', ' ', processed)
        # Strip leading/trailing whitespace
        processed = processed.strip()

        # Step 3: Remove isolated years that might remain
        processed = re.sub(r'\b(?:19|20)\d{2}\b', ' ', processed)
        # Clean up again after year removal
        processed = re.sub(r'\s+', ' ', processed).strip()

        # Step 4: Remove isolated single characters (except for valid initials)
        words = processed.split()
        filtered_words = [
            word for word in words
            if len(word) > 1 or (word.isalpha() and word.isupper())
        ]
        result = ' '.join(filtered_words)

        if not result:
            self.logger.debug(f"Fallback to original: '{original}'")
            # Fallback: try to extract anything that looks like a title
            result = re.sub(r'[^\w\s]', ' ', original).strip()
            result = re.sub(r'\s+', ' ', result).strip()

        self.logger.debug(f"Final result: '{original}' -> '{result}'")
        return result

    def _extract_year(self, filename: str) -> Optional[str]:
        """Extract year from filename with validation."""
        # Find all year matches
        matches = list(self.config._year_regex.finditer(filename))

        if not matches:
            return None

        candidates = []

        for match in matches:
            year_str = match.group()
            year_num = int(year_str)

            # Basic range check
            if not (1900 <= year_num <= 2030):
                continue

            # Context analysis
            start, end = match.start(), match.end()
            context_before = filename[max(0, start-10):start].upper()
            context_after = filename[end:min(len(filename), end+10)].upper()

            # Check if surrounded by tech indicators (strong signal for release year)
            tech_indicators = ['1080', '720', '4K', 'HD', 'BD', 'DVD', 'X264', 'H264', 'AAC']
            has_tech_context = any(ind in context_before or ind in context_after
                                  for ind in tech_indicators)

            # Score the candidate
            score = 0
            if has_tech_context:
                score += 2

            # Prefer years later in the filename (usually after title)
            score += (start / len(filename)) * 0.5

            candidates.append((year_str, score, start))

        if not candidates:
            return None

        # Sort by score (descending), then by position (descending)
        candidates.sort(key=lambda x: (-x[1], -x[2]))
        selected = candidates[0][0]

        self.logger.debug(f"Selected year {selected} from candidates: {candidates}")
        return selected


def scan_movies_from_directory(
    directory: str,
    config_file: Optional[str] = None,
    recursive: bool = True
) -> List[Dict]:
    """Convenience function: scan directory and return results in dictionary format"""
    dir_path = Path(directory)

    # Auto-detect config file
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

    if not config_file:
        raise ValueError("No configuration file found")

    config_obj = MovieFileScannerConfig(Path(config_file))
    scanner = MovieFileScanner(config_obj)
    movie_files = scanner.scan_directory(dir_path, recursive)

    return [
        {
            'file_path': str(m.file_path),
            'movie_name': m.movie_name,
            'year': m.year,
            'extension': m.extension,
            'raw_filename': m.raw_filename
        }
        for m in movie_files
    ]