"""
Logger setup for the Self-Evolving Robot System.
"""

import sys
from pathlib import Path
from loguru import logger as _logger

from .config import get_logging_config, get_storage_config


def setup_logger():
    """Configure and setup the global logger."""
    config = get_logging_config()
    storage_config = get_storage_config()
    
    # Remove default handler
    _logger.remove()
    
    # Add console handler
    if config.console_output:
        _logger.add(
            sys.stdout,
            format=config.log_format,
            level=config.log_level,
        )
    
    # Add file handler
    if config.log_file or True:  # Always log to file
        log_file = Path(config.log_file or storage_config.logs_dir / "robot_system.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        _logger.add(
            log_file,
            format=config.log_format,
            level=config.log_level,
            rotation="500 MB",
            retention="7 days",
        )
    
    return _logger


# Initialize logger
logger = setup_logger()


def get_logger(name: str = None):
    """Get a logger instance (with optional name/module)."""
    # loguru creates separate contexts per name automatically
    if name:
        return _logger.bind(name=name)
    return logger


__all__ = ["logger", "setup_logger", "get_logger"]
