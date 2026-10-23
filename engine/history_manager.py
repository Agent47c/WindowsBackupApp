"""
History Manager Module
Manages backup history — saves BOTH locally and in the backup destination
so history survives Windows reinstallation.
"""

import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from utils.logger import Logger


class HistoryManager:
    """
    Manages backup history with portable storage.
    
    History is saved in TWO places:
    1. Locally (app directory) — for quick access
    2. In the backup destination — survives Windows reinstall
    
    On restore, history can be loaded from the backup folder directly.
    """
    
    HISTORY_FILE = "backup_history.json"
    BACKUP_ROOT_FOLDER = "SmartAppBackup"
    
    def __init__(self, history_dir: str = None):
        """
        Initialize History Manager
        
        Args:
            history_dir: Directory to store local history file (default: app directory)
        """
        self.logger = Logger()
        
        # Use application directory by default (portable)
        if history_dir is None:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            history_dir = os.path.join(app_dir, 'data')
        
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / self.HISTORY_FILE
        self.history_data = self._load_history()
    
    def _create_empty_history(self) -> Dict:
        """Create a new empty history structure"""
        return {
            'version': '2.0',
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'backups': {}
        }
    
    def _load_history(self) -> Dict:
        """
        Load history from local file
        
        Returns:
            History data dictionary
        """
        if not self.history_file.exists():
            return self._create_empty_history()
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info("Loaded backup history")
                return data
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
            return self._create_empty_history()
    
    def _save_history(self) -> None:
        """Save history to local file"""
        try:
            self.history_data['last_updated'] = datetime.now().isoformat()
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=2)
            
            self.logger.info("Saved backup history (local)")
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")
    
    def sync_history_to_backup(self, backup_root: str) -> None:
        """
        Save a copy of the history file in the backup destination.
        This ensures history survives Windows reinstalls.
        
        Args:
            backup_root: Root backup directory (e.g., D:\\MyBackups)
        """
        try:
            smart_backup_dir = os.path.join(backup_root, self.BACKUP_ROOT_FOLDER)
            os.makedirs(smart_backup_dir, exist_ok=True)
            
            dest_file = os.path.join(smart_backup_dir, self.HISTORY_FILE)
            
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=2)
            
            self.logger.info(f"Synced history to backup: {dest_file}")
        except Exception as e:
            self.logger.error(f"Failed to sync history to backup: {e}")
    
    def load_history_from_backup(self, backup_root: str) -> bool:
        """
        Load history from a backup destination folder.
        Used after Windows reinstall when local history is gone.
        
        Args:
            backup_root: Root backup directory (e.g., D:\\MyBackups)
            
        Returns:
            True if history was loaded successfully
        """
        try:
            # Try SmartAppBackup subfolder first
            history_path = os.path.join(
                backup_root, self.BACKUP_ROOT_FOLDER, self.HISTORY_FILE)
            
            if not os.path.exists(history_path):
                # Try the root directly
                history_path = os.path.join(backup_root, self.HISTORY_FILE)
            
            if not os.path.exists(history_path):
                self.logger.warning(f"No history file found in: {backup_root}")
                return False
            
            with open(history_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Merge with existing history
            imported_backups = imported_data.get('backups', {})
            merged_count = 0
            
            for app_name, backup_info in imported_backups.items():
                if app_name not in self.history_data['backups']:
                    self.history_data['backups'][app_name] = backup_info
                    merged_count += 1
                else:
                    # Keep the newer one
                    existing_time = self.history_data['backups'][app_name].get('last_backup', '')
                    imported_time = backup_info.get('last_backup', '')
                    if imported_time > existing_time:
                        self.history_data['backups'][app_name] = backup_info
                        merged_count += 1
            
            self._save_history()
            self.logger.info(
                f"Imported {merged_count} backup entries from: {history_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load history from backup: {e}")
            return False
    
    def scan_backup_folder(self, backup_root: str) -> List[Dict]:
        """
        Scan a backup folder for available backups by finding manifest.json files.
        Works even without history — directly scans the folder structure.
        
        Args:
            backup_root: Root backup directory to scan
            
        Returns:
            List of backup info dicts with 'app_name' and 'backup_path'
        """
        found_backups = []
        
        # Look for SmartAppBackup subfolder
        smart_dir = os.path.join(backup_root, self.BACKUP_ROOT_FOLDER)
        search_dir = smart_dir if os.path.exists(smart_dir) else backup_root
        
        try:
            # Find all manifest.json files
            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)
                if not os.path.isdir(item_path):
                    continue
                
                manifest_path = os.path.join(item_path, 'manifest.json')
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        found_backups.append({
                            'app_name': manifest.get('app_name', item),
                            'backup_path': item_path,
                            'version': manifest.get('app_version', ''),
                            'timestamp': manifest.get('backup_timestamp', '')
                        })
                    except Exception:
                        # Folder has manifest but it's corrupt, still list it
                        found_backups.append({
                            'app_name': item,
                            'backup_path': item_path,
                            'version': '',
                            'timestamp': ''
                        })
            
            self.logger.info(f"Found {len(found_backups)} backups in: {search_dir}")
        except Exception as e:
            self.logger.error(f"Failed to scan backup folder: {e}")
        
        return sorted(found_backups, key=lambda x: x['app_name'])
    
    def add_backup(
        self,
        app_name: str,
        backup_location: str,
        source_paths: Dict[str, List[str]],
        registry_files: List[str],
        system_info: Optional[Dict] = None
    ) -> None:
        """
        Add or update backup entry in history
        
        Args:
            app_name: Application name
            backup_location: Where backup is stored
            source_paths: Source paths that were backed up
            registry_files: Registry files that were exported
            system_info: Complete hardware, system, and user metadata
        """
        timestamp = datetime.now().isoformat()
        
        if not system_info:
            try:
                from utils.system_profiler import SystemProfiler
                system_info = SystemProfiler().get_full_system_metadata()
            except Exception:
                system_info = {}

        backup_entry = {
            'app_name': app_name,
            'backup_location': backup_location,
            'last_backup': timestamp,
            'windows_username': os.environ.get('USERNAME', 'unknown'),
            'system_info': system_info,
            'source_paths': source_paths,
            'registry_files': registry_files,
            'backup_count': 1
        }

        
        # Merge with existing entry if present
        if app_name in self.history_data['backups']:
            existing = self.history_data['backups'][app_name]
            backup_entry['backup_count'] = existing.get('backup_count', 0) + 1
            backup_entry['first_backup'] = existing.get('first_backup', timestamp)
            
            # Merge source paths
            for category in source_paths.keys():
                existing_paths = set(existing.get('source_paths', {}).get(category, []))
                new_paths = set(source_paths.get(category, []))
                backup_entry['source_paths'][category] = list(existing_paths | new_paths)
            
            # Merge registry files
            existing_reg = set(existing.get('registry_files', []))
            new_reg = set(registry_files)
            backup_entry['registry_files'] = list(existing_reg | new_reg)
            
            self.logger.info(f"Merged backup for {app_name} (#{backup_entry['backup_count']})")
        else:
            backup_entry['first_backup'] = timestamp
            self.logger.info(f"Added new backup for {app_name}")
        
        self.history_data['backups'][app_name] = backup_entry
        self._save_history()
    
    def get_backup_history(self, app_name: str = None) -> Optional[Dict]:
        """Get backup history for an application or all"""
        if app_name:
            return self.history_data['backups'].get(app_name)
        return self.history_data['backups']
    
    def get_all_backed_up_apps(self) -> List[str]:
        """Get list of all applications that have been backed up"""
        return sorted(self.history_data['backups'].keys())
    
    def get_backup_location(self, app_name: str) -> Optional[str]:
        """Get backup location for an application"""
        backup = self.history_data['backups'].get(app_name)
        if backup:
            return backup.get('backup_location')
        return None
    
    def remove_backup(self, app_name: str) -> bool:
        """Remove backup entry from history"""
        if app_name in self.history_data['backups']:
            del self.history_data['backups'][app_name]
            self._save_history()
            self.logger.info(f"Removed backup history for {app_name}")
            return True
        return False
    
    def get_history_file_path(self) -> str:
        """Get path to local history file"""
        return str(self.history_file)
    
    def has_history(self) -> bool:
        """Check if any backup history exists"""
        return bool(self.history_data.get('backups'))
    
    def get_backup_summary(self) -> Dict:
        """Get summary of all backups"""
        total_backups = len(self.history_data['backups'])
        total_operations = sum(
            backup.get('backup_count', 1) 
            for backup in self.history_data['backups'].values()
        )
        
        most_recent = None
        if self.history_data['backups']:
            most_recent_app = max(
                self.history_data['backups'].items(),
                key=lambda x: x[1].get('last_backup', '')
            )
            most_recent = {
                'app_name': most_recent_app[0],
                'timestamp': most_recent_app[1].get('last_backup')
            }
        
        return {
            'total_applications': total_backups,
            'total_backup_operations': total_operations,
            'most_recent_backup': most_recent,
            'history_file': str(self.history_file)
        }
