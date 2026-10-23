"""
Path Utilities Module
Handles environment variable expansion and path validation
"""

import os
from pathlib import Path
from typing import List
from utils.logger import Logger


class PathUtils:
    """Utility functions for path handling"""
    
    # Forbidden paths that should never be backed up
    FORBIDDEN_PATHS = [
        'C:\\Windows\\System32',
        'C:\\Windows\\SysWOW64',
        'C:\\Windows\\WinSxS',
        '$Recycle.Bin',
        'System Volume Information',
        'C:\\Windows\\Temp',
        'C:\\Windows\\Driver',
    ]
    
    @staticmethod
    def expand_environment_variables(path: str) -> str:
        """
        Expand Windows environment variables in path
        
        Args:
            path: Path potentially containing environment variables
            
        Returns:
            Expanded absolute path
        """
        return os.path.expandvars(path)
    
    @staticmethod
    def is_safe_path(path: str) -> bool:
        """
        Check if path is safe to backup/restore
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safe
        """
        logger = Logger()
        expanded_path = PathUtils.expand_environment_variables(path).lower()
        
        # Check against forbidden paths
        for forbidden in PathUtils.FORBIDDEN_PATHS:
            if forbidden.lower() in expanded_path:
                logger.warning(f"Unsafe path detected: {path}")
                return False
        
        return True
    
    @staticmethod
    def path_exists(path: str) -> bool:
        """
        Check if path exists after expanding variables
        
        Args:
            path: Path to check
            
        Returns:
            True if path exists
        """
        try:
            expanded = PathUtils.expand_environment_variables(path)
            return Path(expanded).exists()
        except Exception:
            return False
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """
        Ensure directory exists, create if necessary
        
        Args:
            path: Directory path
        """
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def filter_existing_paths(paths: List[str]) -> List[str]:
        """
        Filter list to only include existing paths
        
        Args:
            paths: List of paths to filter
            
        Returns:
            List of existing paths
        """
        logger = Logger()
        existing = []
        
        for path in paths:
            if PathUtils.path_exists(path):
                existing.append(path)
            else:
                expanded = PathUtils.expand_environment_variables(path)
                logger.warning(f"Path does not exist: {expanded}")
        
        return existing
