"""
Backup Engine Module
Handles the backup process for applications
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from engine.registry_manager import RegistryManager
from engine.manifest_manager import ManifestManager
from engine.history_manager import HistoryManager
from utils.logger import Logger
from utils.path_utils import PathUtils


class BackupEngine:
    """Handles application backup operations"""
    
    BACKUP_ROOT_FOLDER = "SmartAppBackup"
    
    def __init__(self):
        """Initialize Backup Engine"""
        self.logger = Logger()
        self.registry_manager = RegistryManager()
        self.manifest_manager = ManifestManager()
        self.history_manager = HistoryManager()
        self.progress_callback: Optional[Callable[[str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function for progress updates
        
        Args:
            callback: Function to call with progress messages
        """
        self.progress_callback = callback
    
    def _update_progress(self, message: str) -> None:
        """Send progress update to callback"""
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def backup_application(
        self,
        app_name: str,
        data_paths: Dict[str, List[str]],
        destination_root: str,
        app_version: str = None  # Add this parameter
    ) -> bool:
        """
        Perform backup of application
        
        Args:
            app_name: Application name
            data_paths: Dictionary with 'program_data', 'user_data', 'registry_keys' lists
            destination_root: Root destination directory (e.g., D:\\ or folder path)
            
        Returns:
            True if backup successful
        """
        try:
            self._update_progress(f"Starting backup for: {app_name}")
            
            # Create backup directory structure
            backup_dir = self._create_backup_structure(destination_root, app_name)
            
            # Backup program data
            program_data_paths = self._backup_directories(
                data_paths.get('program_data', []),
                os.path.join(backup_dir, "ProgramData"),
                "Program Data"
            )
            
            # Backup user data
            user_data_paths = self._backup_directories(
                data_paths.get('user_data', []),
                os.path.join(backup_dir, "UserData"),
                "User Data"
            )
            
            # Backup custom locations (non-standard paths like D:\Games)
            custom_paths = self._backup_custom_locations(
                data_paths.get('custom_locations', []),
                os.path.join(backup_dir, "CustomLocations")
            )
            
            # Backup Start Menu and Desktop shortcuts
            shortcut_paths = self._backup_shortcuts(
                data_paths.get('shortcuts', []),
                os.path.join(backup_dir, "Shortcuts")
            )
            
            # Backup registry
            registry_files = self._backup_registry(
                data_paths.get('registry_keys', []),
                os.path.join(backup_dir, "Registry")
            )
            
            # Create manifest
            source_paths = {
                'program_data': program_data_paths,
                'user_data': user_data_paths,
                'custom_locations': custom_paths,
                'shortcuts': shortcut_paths
            }
            
            manifest_path = self.manifest_manager.create_manifest(
                app_name,
                backup_dir,
                source_paths,
                registry_files,
                app_version
            )
            
            # Add to history
            self.history_manager.add_backup(
                app_name,
                backup_dir,
                source_paths,
                [os.path.basename(f) for f in registry_files]
            )
            
            # Sync history to backup destination (survives Windows reinstall)
            self.history_manager.sync_history_to_backup(destination_root)
            
            # Mark backup folder as hidden (optional)
            self._hide_backup_folder(os.path.join(destination_root, self.BACKUP_ROOT_FOLDER))
            
            self._update_progress(f"Backup completed successfully: {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            self._update_progress(f"Backup failed: {e}")
            return False
    
    def _create_backup_structure(self, destination_root: str, app_name: str) -> str:
        """
        Create backup directory structure with organized folders

        Args:
            destination_root: Root destination directory
            app_name: Application name

        Returns:
            Path to application backup directory
        """
        # Create: <Destination>/SmartAppBackup/<AppName>/
        backup_root = os.path.join(destination_root, self.BACKUP_ROOT_FOLDER)
        app_backup_dir = os.path.join(backup_root, app_name)

        # Create ProgramData subdirectories
        program_data_dir = os.path.join(app_backup_dir, "ProgramData")
        PathUtils.ensure_directory(os.path.join(program_data_dir, "ProgramFiles"))
        PathUtils.ensure_directory(os.path.join(program_data_dir, "ProgramFiles_x86"))
        PathUtils.ensure_directory(os.path.join(program_data_dir, "ProgramData"))

        # Create UserData subdirectories
        user_data_dir = os.path.join(app_backup_dir, "UserData")
        PathUtils.ensure_directory(os.path.join(user_data_dir, "Roaming"))
        PathUtils.ensure_directory(os.path.join(user_data_dir, "Local"))
        PathUtils.ensure_directory(os.path.join(user_data_dir, "LocalLow"))
        PathUtils.ensure_directory(os.path.join(user_data_dir, "Documents"))
        PathUtils.ensure_directory(os.path.join(user_data_dir, "PublicDocuments"))

        # Create Registry directory
        PathUtils.ensure_directory(os.path.join(app_backup_dir, "Registry"))

        # Create Shortcuts directory
        PathUtils.ensure_directory(os.path.join(app_backup_dir, "Shortcuts"))

        self._update_progress(f"Created backup structure: {app_backup_dir}")
        return app_backup_dir

    def _backup_directories(self,source_paths: List[str],destination: str,category: str) -> List[str]:
        """
        Backup directories to organized destination

        Args:
            source_paths: List of source directory paths
            destination: Base destination directory (ProgramData or UserData)
            category: Category name for logging

        Returns:
            List of successfully backed up source paths
        """
        backed_up_paths = []

        for source_path in source_paths:
            # Expand environment variables
            expanded_source = PathUtils.expand_environment_variables(source_path)

            # Validate path safety
            if not PathUtils.is_safe_path(source_path):
                self.logger.warning(f"Skipping unsafe path: {source_path}")
                continue

            # Check if path exists
            if not PathUtils.path_exists(source_path):
                self.logger.warning(f"Path does not exist, skipping: {expanded_source}")
                continue

            try:
                # Determine the correct subdirectory based on source location
                subdest = self._get_organized_destination(expanded_source, destination, category)

                # Create destination subdirectory name
                dir_name = os.path.basename(expanded_source)
                dest_path = os.path.join(subdest, dir_name)

                # Copy directory tree
                self._update_progress(f"Copying {category}: {dir_name}")
                shutil.copytree(expanded_source, dest_path, dirs_exist_ok=True)

                backed_up_paths.append(source_path)
                self.logger.info(f"Backed up: {expanded_source} -> {dest_path}")

            except Exception as e:
                self.logger.error(f"Failed to backup {expanded_source}: {e}")

        return backed_up_paths

    def _get_organized_destination(self, source_path: str, base_dest: str, category: str) -> str:
        """
        Determine organized destination folder based on source location

        Args:
            source_path: Source file path
            base_dest: Base destination (ProgramData or UserData folder)
            category: "Program Data" or "User Data"

        Returns:
            Organized destination path
        """
        source_lower = source_path.lower()

        if category == "Program Data":
            # Check if from Program Files (x86)
            if 'program files (x86)' in source_lower or 'program files(x86)' in source_lower:
                return os.path.join(base_dest, "ProgramFiles_x86")
            # Check if from Program Files
            elif 'program files' in source_lower:
                return os.path.join(base_dest, "ProgramFiles")
            # Check if from ProgramData
            elif 'programdata' in source_lower:
                return os.path.join(base_dest, "ProgramData")
            else:
                # Default to ProgramData subfolder
                return os.path.join(base_dest, "ProgramData")

        elif category == "User Data":
            if 'public\\documents' in source_lower or 'public/documents' in source_lower:
                return os.path.join(base_dest, "PublicDocuments")
            elif '\\documents' in source_lower or '/documents' in source_lower:
                return os.path.join(base_dest, "Documents")
            # Check if from Roaming
            elif 'appdata\\roaming' in source_lower or 'appdata/roaming' in source_lower:
                return os.path.join(base_dest, "Roaming")
            # Check if from Local
            elif 'appdata\\local\\' in source_lower or 'appdata/local/' in source_lower:
                # Exclude LocalLow
                if 'locallow' not in source_lower:
                    return os.path.join(base_dest, "Local")
                else:
                    return os.path.join(base_dest, "LocalLow")
            # Check if from LocalLow
            elif 'locallow' in source_lower:
                return os.path.join(base_dest, "LocalLow")
            else:
                # Default to Roaming
                return os.path.join(base_dest, "Roaming")

        return base_dest


    
    def _backup_registry(self, registry_keys: List[str], destination: str) -> List[str]:
        """
        Backup registry keys
        
        Args:
            registry_keys: List of registry key paths
            destination: Destination directory for .reg files
            
        Returns:
            List of exported .reg file paths
        """
        if not registry_keys:
            self.logger.info("No registry keys to backup")
            return []
        
        self._update_progress("Exporting registry keys...")
        registry_files = self.registry_manager.export_registry_keys(registry_keys, destination)
        
        self._update_progress(f"Exported {len(registry_files)} registry keys")
        return registry_files
    
    def _hide_backup_folder(self, folder_path: str) -> None:
        """
        Mark backup folder as hidden (Windows)
        
        Args:
            folder_path: Path to folder to hide
        """
        try:
            if os.name == 'nt' and os.path.exists(folder_path):
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(folder_path, FILE_ATTRIBUTE_HIDDEN)
                self.logger.info(f"Marked folder as hidden: {folder_path}")
        except Exception as e:
            self.logger.warning(f"Could not hide folder: {e}")
    
    def _backup_custom_locations(
        self,
        custom_paths: List[str],
        destination: str
    ) -> List[str]:
        """
        Backup custom/non-standard locations
        
        Args:
            custom_paths: List of custom directory paths
            destination: Destination directory for custom backups
            
        Returns:
            List of successfully backed up paths
        """
        if not custom_paths:
            return []
        
        backed_up = []
        PathUtils.ensure_directory(destination)
        
        for source_path in custom_paths:
            if not os.path.exists(source_path):
                continue
            
            if not PathUtils.is_safe_path(source_path):
                self.logger.warning(f"Skipping unsafe custom path: {source_path}")
                continue
            
            try:
                dir_name = os.path.basename(source_path)
                dest_path = os.path.join(destination, dir_name)
                
                self._update_progress(f"Copying custom location: {dir_name}")
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                
                backed_up.append(source_path)
                self.logger.info(f"Backed up custom: {source_path} -> {dest_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to backup custom path {source_path}: {e}")
        
        return backed_up

    def _backup_shortcuts(
        self,
        shortcut_paths: List[str],
        destination: str
    ) -> List[str]:
        """
        Backup Start Menu and Desktop shortcuts
        
        These are essential for Windows to show the app in search/Start Menu.
        We store them with their original paths in a metadata file for restore.
        
        Args:
            shortcut_paths: List of shortcut file/folder paths
            destination: Destination directory for shortcuts
            
        Returns:
            List of successfully backed up shortcut paths (original paths)
        """
        if not shortcut_paths:
            return []
        
        import json
        backed_up = []
        PathUtils.ensure_directory(destination)
        shortcut_metadata = []
        
        for source_path in shortcut_paths:
            if not os.path.exists(source_path):
                continue
            
            try:
                item_name = os.path.basename(source_path)
                dest_path = os.path.join(destination, item_name)
                
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                    self._update_progress(f"Backed up shortcut folder: {item_name}")
                elif os.path.isfile(source_path):
                    shutil.copy2(source_path, dest_path)
                    self._update_progress(f"Backed up shortcut: {item_name}")
                
                # Record the original path for restore
                shortcut_metadata.append({
                    'name': item_name,
                    'original_path': source_path,
                    'is_directory': os.path.isdir(source_path)
                })
                
                backed_up.append(source_path)
                self.logger.info(f"Backed up shortcut: {source_path} -> {dest_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to backup shortcut {source_path}: {e}")
        
        # Save metadata for restore
        if shortcut_metadata:
            metadata_path = os.path.join(destination, "_shortcut_metadata.json")
            try:
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(shortcut_metadata, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to save shortcut metadata: {e}")
        
        return backed_up
