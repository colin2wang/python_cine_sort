"""
Logging configuration utility module
Provides unified logging configuration and management functionality
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class LogConfig:
    """Logging configuration class"""
    
    def __init__(self):
        self.logger_name = "python_cine_sort"
        self.log_level = logging.INFO
        self.log_format = (
            '%(asctime)s | %(levelname)-8s | %(name)s | '
            '%(filename)s:%(lineno)d | %(message)s'
        )
        self.date_format = '%Y-%m-%d %H:%M:%S'
        self.log_dir = Path("logs")
        self.max_bytes = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.enable_console = True
        self.enable_file = False
        
    def set_log_level(self, level: Union[int, str]):
        """Set logging level"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.log_level = level
        
    def set_logger_name(self, name: str):
        """Set logger name"""
        self.logger_name = name
        
    def set_log_directory(self, log_dir: Union[str, Path]):
        """Set log directory"""
        self.log_dir = Path(log_dir)
        
    def disable_console(self):
        """Disable console output"""
        self.enable_console = False
        
    def disable_file_logging(self):
        """Disable file logging"""
        self.enable_file = False


def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """
    Configure and return logger
    
    Args:
        config: Logging configuration object, if None uses default configuration
        
    Returns:
        logging.Logger: Configured logger
    """
    if config is None:
        config = LogConfig()
    
    # 创建日志记录器
    logger = logging.getLogger(config.logger_name)
    logger.setLevel(config.log_level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt=config.log_format,
        datefmt=config.date_format
    )
    
    # 控制台处理器
    if config.enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(config.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if config.enable_file:
        # 确保日志目录存在
        config.log_dir.mkdir(exist_ok=True)
        
        # 生成日志文件名（按日期）
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = config.log_dir / f"{config.logger_name}_{today}.log"
        
        # 文件处理器（带轮转）
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(config.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger
    
    Args:
        name: Logger name, if None uses default name
        
    Returns:
        logging.Logger: Logger instance
    """
    if name is None:
        name = "python_cine_sort"
    
    return logging.getLogger(name)


# 默认配置的便捷函数
def setup_default_logging(log_level: Union[int, str] = logging.INFO) -> logging.Logger:
    """
    Set up default logging configuration
    
    Args:
        log_level: Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    config = LogConfig()
    config.set_log_level(log_level)
    return setup_logging(config)


def setup_debug_logging() -> logging.Logger:
    """Set up debug level logging"""
    return setup_default_logging(logging.DEBUG)


def setup_error_logging() -> logging.Logger:
    """Set up error level logging"""
    return setup_default_logging(logging.ERROR)


# 全局日志记录器实例
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """
    Get default logger (singleton pattern)
    
    Returns:
        logging.Logger: Default logger
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_default_logging()
    return _default_logger


# 便捷的日志函数
def debug(message: str, *args, **kwargs):
    """Debug log"""
    get_default_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Info log"""
    get_default_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Warning log"""
    get_default_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Error log"""
    get_default_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Critical error log"""
    get_default_logger().critical(message, *args, **kwargs)


# 上下文管理器用于临时修改日志级别
class LogLevelContext:
    """Logging level context manager"""
    
    def __init__(self, logger: logging.Logger, temp_level: int):
        self.logger = logger
        self.temp_level = temp_level
        self.original_level = logger.level
        
    def __enter__(self):
        self.logger.setLevel(self.temp_level)
        return self.logger
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)


# 异常处理装饰器
def log_exceptions(logger: Optional[logging.Logger] = None):
    """
    Decorator: Automatically log function exceptions
    
    Args:
        logger: Logger, if None uses default logger
    """
    if logger is None:
        logger = get_default_logger()
        
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception occurred in function {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试代码
    logger = setup_debug_logging()
    
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")
    
    # 测试便捷函数
    info("使用便捷函数记录信息")
    error("使用便捷函数记录错误")
    
    # 测试上下文管理器
    with LogLevelContext(logger, logging.DEBUG):
        logger.info("临时提升到DEBUG级别")
        
    logger.info("恢复原来的日志级别")