"""
Manifest Manager Module
Handles backup metadata creation and validation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from utils.logger import Logger
from utils.system_profiler import SystemProfiler


class ManifestManager:
    """Manages backup manifest files"""
    
    MANIFEST_VERSION = "2.0.0"
    MANIFEST_FILENAME = "manifest.json"
    
    def __init__(self):
        """Initialize Manifest Manager"""
        self.logger = Logger()
        self.profiler = SystemProfiler()
    
    def create_manifest(
        self,
        app_name: str,
        backup_dir: str,
        source_paths: Dict[str, List[str]],
        registry_files: List[str],
        app_version: str = None
    ) -> str:
        """
        Create a backup manifest file with full hardware and system metadata
    
        Args:
            app_name: Application name
            backup_dir: Backup directory path
            source_paths: Dictionary with 'program_data' and 'user_data' path lists
            registry_files: List of exported registry files
            app_version: Application version (optional)
        
        Returns:
            Path to created manifest file
        """
        manifest_path = os.path.join(backup_dir, self.MANIFEST_FILENAME)
        system_metadata = self.profiler.get_full_system_metadata()
        
        manifest_data = {
            'manifest_version': self.MANIFEST_VERSION,
            'app_name': app_name,
            'app_version': app_version or 'Unknown',
            'backup_timestamp': datetime.now().isoformat(),
            'windows_username': os.environ.get('USERNAME', 'unknown'),
            'system_info': system_metadata,
            'source_paths': source_paths,
            'registry_files': [os.path.basename(f) for f in registry_files],
            'backup_directory': backup_dir
        }
        
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2)
            
            self.logger.info(f"Created manifest with system metadata: {manifest_path}")
            return manifest_path
            
        except Exception as e:
            self.logger.error(f"Failed to create manifest: {e}")
            raise

    
    def load_manifest(self, manifest_path: str) -> Optional[Dict]:
        """
        Load and validate manifest file
        
        Args:
            manifest_path: Path to manifest.json file
            
        Returns:
            Manifest data dictionary or None if invalid
        """
        if not os.path.exists(manifest_path):
            self.logger.error(f"Manifest file not found: {manifest_path}")
            return None
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Validate required fields
            required_fields = [
                'app_name', 'app_version', 'backup_timestamp', 'windows_username',
                'source_paths', 'registry_files','backup_directory'
            ]
            
            for field in required_fields:
                if field not in manifest_data:
                    self.logger.error(f"Invalid manifest: missing field '{field}'")
                    return None
            
            self.logger.info(f"Loaded manifest for: {manifest_data['app_name']}")
            return manifest_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in manifest: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading manifest: {e}")
            return None
    
    def find_manifest_in_directory(self, directory: str) -> Optional[str]:
        """
        Find manifest.json file in directory
        
        Args:
            directory: Directory to search
            
        Returns:
            Path to manifest file or None
        """
        manifest_path = os.path.join(directory, self.MANIFEST_FILENAME)
        
        if os.path.exists(manifest_path):
            return manifest_path
        
        # Search in subdirectories (one level deep)
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    sub_manifest = os.path.join(item_path, self.MANIFEST_FILENAME)
                    if os.path.exists(sub_manifest):
                        return sub_manifest
        except Exception as e:
            self.logger.error(f"Error searching for manifest: {e}")
        
        return None
    
    def validate_backup_structure(self, backup_dir: str) -> bool:
        """
        Validate backup directory structure
        
        Args:
            backup_dir: Backup directory path
            
        Returns:
            True if structure is valid
        """
        required_items = [self.MANIFEST_FILENAME]
        
        for item in required_items:
            if not os.path.exists(os.path.join(backup_dir, item)):
                self.logger.error(f"Missing required file: {item}")
                return False
        
        return True
