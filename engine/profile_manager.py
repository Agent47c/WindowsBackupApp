"""
Profile Manager Module
Handles loading and validation of application backup profiles
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from utils.logger import Logger


@dataclass
class ApplicationProfile:
    """Data class representing an application backup profile"""
    app_name: str
    program_data_paths: List[str]
    user_data_paths: List[str]
    registry_keys: List[str]
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary"""
        return {
            'app_name': self.app_name,
            'program_data_paths': self.program_data_paths,
            'user_data_paths': self.user_data_paths,
            'registry_keys': self.registry_keys
        }


class ProfileManager:
    """Manages application backup profiles"""
    
    def __init__(self, profiles_dir: str = "profiles"):
        """
        Initialize the Profile Manager
        
        Args:
            profiles_dir: Directory containing profile JSON files
        """
        self.profiles_dir = Path(profiles_dir)
        self.logger = Logger()
        self.profiles: Dict[str, ApplicationProfile] = {}
        
        # Create profiles directory if it doesn't exist
        self.profiles_dir.mkdir(exist_ok=True)
        
        # Load all profiles
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Scan and load all profile JSON files"""
        if not self.profiles_dir.exists():
            self.logger.warning(f"Profiles directory not found: {self.profiles_dir}")
            return
        
        json_files = list(self.profiles_dir.glob("*.json"))
        
        if not json_files:
            self.logger.warning("No profile files found in profiles directory")
            return
        
        for json_file in json_files:
            try:
                self._load_profile_file(json_file)
            except Exception as e:
                self.logger.error(f"Failed to load profile {json_file.name}: {e}")
    
    def _load_profile_file(self, filepath: Path) -> None:
        """
        Load a single profile JSON file
        
        Args:
            filepath: Path to the JSON file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['app_name', 'program_data_paths', 'user_data_paths', 'registry_keys']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create profile object
        profile = ApplicationProfile(
            app_name=data['app_name'],
            program_data_paths=data['program_data_paths'],
            user_data_paths=data['user_data_paths'],
            registry_keys=data['registry_keys']
        )
        
        self.profiles[profile.app_name] = profile
        self.logger.info(f"Loaded profile: {profile.app_name}")
    
    def get_profile(self, app_name: str) -> Optional[ApplicationProfile]:
        """
        Get a profile by application name
        
        Args:
            app_name: Name of the application
            
        Returns:
            ApplicationProfile or None if not found
        """
        return self.profiles.get(app_name)
    
    def get_profile_names(self) -> List[str]:
        """
        Get list of all available profile names
        
        Returns:
            List of profile names
        """
        return sorted(self.profiles.keys())
    
    def profile_exists(self, app_name: str) -> bool:
        """
        Check if a profile exists
        
        Args:
            app_name: Name of the application
            
        Returns:
            True if profile exists
        """
        return app_name in self.profiles
