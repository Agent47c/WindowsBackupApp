"""
Logging System Module
Handles all application logging with timestamps and detailed error files
"""

import logging
import os
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """Singleton logger for application-wide logging"""
    
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        """Ensure singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self) -> None:
        """Initialize the logging system"""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file & persistent error log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"backup_tool_{timestamp}.log"
        error_log_file = logs_dir / "smartbackup_errors.log"
        
        # Configure logger
        self._logger = logging.getLogger("SmartAppBackup")
        self._logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Dedicated Error handler for detailed troubleshooting
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter with line numbers and file names
        formatter = logging.Formatter(
            '%(asctime)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self._logger.addHandler(file_handler)
        self._logger.addHandler(error_handler)
        self._logger.addHandler(console_handler)
        
        self.log_file_path = str(log_file)
        self.error_file_path = str(error_log_file)
        self.logs_dir_path = str(logs_dir.resolve())
        self.info("Logger initialized")
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        if self._logger:
            self._logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message"""
        if self._logger:
            self._logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        if self._logger:
            self._logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        if self._logger:
            self._logger.error(message)

    def log_exception(self, exc: Exception, context: str = "") -> None:
        """Log full exception traceback with file and line details"""
        tb_str = traceback.format_exc()
        msg = f"{context} - Exception: {type(exc).__name__}: {exc}\n{tb_str}"
        self.error(msg)
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        if self._logger:
            self._logger.critical(message)
    
    def get_log_file_path(self) -> str:
        """Get the current log file path"""
        return self.log_file_path

    def get_logs_dir(self) -> str:
        """Get absolute path to logs directory"""
        return self.logs_dir_path

