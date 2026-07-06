"""
Logging configuration for Consolidated AI Portal
Provides centralized logging to file and console with timestamps
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: Path = None):
    """
    Setup comprehensive logging configuration
    
    Args:
        log_dir: Directory to store log files. Defaults to ./logs
    
    Returns:
        logger: Configured logger instance
    """
    
    if log_dir is None:
        log_dir = Path(__file__).parent / "logs"
    
    log_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler - DEBUG level (verbose)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler - INFO level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Get application logger
    logger = logging.getLogger(__name__)
    logger.info(f"✓ Logging initialized")
    logger.info(f"✓ Log file: {log_file}")
    logger.info(f"✓ Log directory: {log_dir}")
    
    return logger, log_file, log_dir


def get_logger(name: str):
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)


def enable_debug_logging():
    """Enable debug logging for all loggers"""
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)
