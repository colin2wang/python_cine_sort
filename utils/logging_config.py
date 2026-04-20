import logging
import sys
from datetime import datetime
from pathlib import Path


# ==========================================
# Root Directory Detection
# ==========================================
def get_project_root() -> Path:
    """
    Attempts to determine the project root directory by searching
    upward for common project markers (.git, requirements.txt, etc).

    If no marker is found, falls back to the current working directory.
    """
    current_path = Path(__file__).resolve().parent

    # List of files/directories that indicate the root of a project
    markers = ['.git', 'pyproject.toml', 'requirements.txt', 'setup.py', '.env']

    # Traverse up the directory tree
    for _ in range(10):  # Limit recursion depth
        for marker in markers:
            if (current_path / marker).exists():
                return current_path

        parent = current_path.parent
        if parent == current_path:
            # Reached file system root without finding a marker
            break
        current_path = parent

    # Fallback: use the directory where the script was executed
    return Path.cwd()


# ==========================================
# Global Configuration
# ==========================================

# 1. Determine Project Root
PROJECT_ROOT = get_project_root()

# 2. Define Log Directory (Always in project_root/logs)
LOG_DIR = PROJECT_ROOT / 'logs'

# 3. Create Directory if it doesn't exist
try:
    LOG_DIR.mkdir(exist_ok=True)
except OSError as e:
    # Use sys.stderr because logger isn't ready yet
    sys.stderr.write(f"Error creating log directory at {LOG_DIR}: {e}\n")

# 4. Generate Unique Filename (One per run)
_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
LOG_FILE_NAME = f"cloud_music_{_timestamp}.log"
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME

# 5. Define Formats
LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = None, level: str = 'INFO') -> logging.Logger:
    """
    Initializes and returns a logger with console and file handlers.
    The log file is always located in {PROJECT_ROOT}/logs/.

    Args:
        name (str): Logger name (usually __name__).
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        logging.Logger: Configured logger.
    """

    # Initialize logger
    logger = logging.getLogger(name)

    # Set Level
    level_upper = level.upper()
    log_level = getattr(logging, level_upper, logging.INFO)
    logger.setLevel(log_level)

    # Prevent adding duplicate handlers if function is called repeatedly
    if logger.hasHandlers():
        return logger

    # Create Formatter
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Handler 1: Console (Standard Output) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Handler 2: File (Project Root/logs) ---
    try:
        # Convert Path object to string for FileHandler
        file_path_str = str(LOG_FILE_PATH)
        file_handler = logging.FileHandler(file_path_str, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file writing fails
        sys.stderr.write(f"Failed to initialize file handler: {e}\n")

    # Optional: Log the absolute path on initialization for debugging
    if name is None or name == "__main__":
        logger.debug(f"Log file initialized at: {LOG_FILE_PATH}")

    return logger


# ==========================================
# Usage Example
# ==========================================
if __name__ == "__main__":
    # Example usage
    log = setup_logger("test_logger", level="DEBUG")

    print(f"Project Root detected as: {PROJECT_ROOT}")

    log.info("This message \n goes to console \n and the log file \n in root/logs.")
    log.warning(f"Check the file: {LOG_FILE_PATH}")