"""
Restore Engine Module
Handles the restore process for application backups
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
from engine.registry_manager import RegistryManager
from engine.manifest_manager import ManifestManager
from utils.logger import Logger
from utils.path_utils import PathUtils


class RestoreEngine:
    """Handles application restore operations"""
    
    def __init__(self):
        """Initialize Restore Engine"""
        self.logger = Logger()
        self.registry_manager = RegistryManager()
        self.manifest_manager = ManifestManager()
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
    
    def restore_application(
        self,
        backup_path: str,
        overwrite: bool = False
    ) -> bool:
        """
        Restore application from backup
        
        Args:
            backup_path: Path to backup folder or manifest file
            overwrite: Whether to overwrite existing files
            
        Returns:
            True if restore successful
        """
        try:
            # Find and load manifest
            manifest_path = self._find_manifest(backup_path)
            if not manifest_path:
                self._update_progress("Error: Could not find manifest file")
                return False
            
            manifest = self.manifest_manager.load_manifest(manifest_path)
            if not manifest:
                self._update_progress("Error: Invalid manifest file")
                return False
            
            backup_dir = os.path.dirname(manifest_path)
            app_name = manifest['app_name']
            
            self._update_progress(f"Starting restore for: {app_name}")
            
            # Validate backup structure
            if not self.manifest_manager.validate_backup_structure(backup_dir):
                self._update_progress("Error: Invalid backup structure")
                return False
            
            # Restore program data
            p_copied, p_failed = self._restore_directories(
                manifest.get('source_paths', {}).get('program_data', []),
                os.path.join(backup_dir, "ProgramData"),
                "Program Data",
                overwrite
            )
            
            # Restore user data
            u_copied, u_failed = self._restore_directories(
                manifest.get('source_paths', {}).get('user_data', []),
                os.path.join(backup_dir, "UserData"),
                "User Data",
                overwrite
            )
            # Restore custom locations (if any)
            self._restore_custom_locations(manifest, backup_dir, overwrite)
            
            # Restore Start Menu and Desktop shortcuts
            self._restore_shortcuts(os.path.join(backup_dir, "Shortcuts"))
            
            # Restore registry (MUST be after files are in place)
            self._restore_registry(
                manifest.get('registry_files', []),
                os.path.join(backup_dir, "Registry")
            )
            
            total_copied = p_copied + u_copied
            total_failed = p_failed + u_failed

            if total_failed > 0 and total_copied == 0:
                self._update_progress("❌ Restore failed: Access Denied when restoring files. Administrator privileges required!")
                return False
            elif total_failed > 0:
                self._update_progress(f"⚠️ Restore completed with warnings ({total_copied} restored, {total_failed} failed due to permissions)")
                return True

            self._update_progress(f"Restore completed successfully ({total_copied} files restored)")
            return True

            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            self._update_progress(f"Restore failed: {e}")
            return False
    
    def _find_manifest(self, backup_path: str) -> Optional[str]:
        """
        Find manifest file from given path
        
        Args:
            backup_path: Path to backup folder or manifest file
            
        Returns:
            Path to manifest file or None
        """
        # If path is directly to manifest file
        if os.path.isfile(backup_path) and backup_path.endswith('.json'):
            return backup_path
        
        # If path is a directory
        if os.path.isdir(backup_path):
            return self.manifest_manager.find_manifest_in_directory(backup_path)
        
        return None
    
    def _restore_directories(self, original_paths: List[str], backup_source: str, category: str, overwrite: bool) -> tuple[int, int]:
        """
        Restore directories from organized backup structure

        Args:
            original_paths: Original source paths from manifest
            backup_source: Backup source directory (ProgramData or UserData)
            category: Category name for logging
            overwrite: Whether to overwrite existing files

        Returns:
            Tuple of (total_copied, total_failed)
        """
        if not os.path.exists(backup_source):
            self.logger.warning(f"Backup source not found: {backup_source}")
            return (0, 0)

        self.logger.info(f"Restoring {category} from: {backup_source}")

        # For organized structure, scan subdirectories
        if category == "Program Data":
            return self._restore_program_data(backup_source, original_paths, overwrite)
        elif category == "User Data":
            return self._restore_user_data(backup_source, original_paths, overwrite)
        else:
            return self._restore_flat_structure(backup_source, original_paths, category, overwrite)

    def _restore_program_data(self, backup_source: str, original_paths: List[str], overwrite: bool) -> tuple[int, int]:
        """
        Restore program data from organized structure:
        ProgramData/ProgramFiles/, ProgramData/ProgramFiles_x86/, ProgramData/ProgramData/
        """
        total_copied = 0
        total_failed = 0

        subdirs_map = {
            'ProgramFiles': os.path.expandvars('%ProgramFiles%'),
            'ProgramFiles_x86': os.path.expandvars('%ProgramFiles(x86)%'),
            'ProgramData': os.path.expandvars('%ProgramData%')
        }

        for subdir_name, base_restore_path in subdirs_map.items():
            subdir_path = os.path.join(backup_source, subdir_name)

            if not os.path.exists(subdir_path):
                continue

            try:
                for item in os.listdir(subdir_path):
                    item_path = os.path.join(subdir_path, item)

                    if not os.path.isdir(item_path):
                        continue

                    target_path = self._find_restore_target(item, original_paths, base_restore_path)

                    if target_path:
                        c, f = self._restore_single_directory(item_path, target_path, item, overwrite)
                        total_copied += c
                        total_failed += f
                    else:
                        self.logger.warning(f"Could not find restore target for: {item}")

            except Exception as e:
                self.logger.error(f"Error restoring from {subdir_name}: {e}")

        return (total_copied, total_failed)

    def _restore_user_data(self, backup_source: str, original_paths: List[str], overwrite: bool) -> tuple[int, int]:
        """
        Restore user data from organized structure:
        UserData/Roaming/, UserData/Local/, UserData/LocalLow/
        """
        total_copied = 0
        total_failed = 0

        subdirs_map = {
            'Roaming': os.path.expandvars('%APPDATA%'),
            'Local': os.path.expandvars('%LOCALAPPDATA%'),
            'LocalLow': os.path.join(os.path.expandvars('%USERPROFILE%'), 'AppData', 'LocalLow'),
            'Documents': os.path.join(os.path.expandvars('%USERPROFILE%'), 'Documents'),
            'PublicDocuments': os.path.join('C:\\', 'Users', 'Public', 'Documents')
        }

        for subdir_name, base_restore_path in subdirs_map.items():
            subdir_path = os.path.join(backup_source, subdir_name)

            if not os.path.exists(subdir_path):
                continue

            try:
                for item in os.listdir(subdir_path):
                    item_path = os.path.join(subdir_path, item)

                    if not os.path.isdir(item_path):
                        continue

                    target_path = self._find_restore_target(item, original_paths, base_restore_path)

                    if target_path:
                        c, f = self._restore_single_directory(item_path, target_path, item, overwrite)
                        total_copied += c
                        total_failed += f
                    else:
                        self.logger.warning(f"Could not find restore target for: {item}")

            except Exception as e:
                self.logger.error(f"Error restoring from {subdir_name}: {e}")

        return (total_copied, total_failed)

    def _find_restore_target(self, folder_name: str, original_paths: List[str], base_path: str) -> Optional[str]:
        """
        Find the correct restore target path
        """
        for original_path in original_paths:
            expanded = PathUtils.expand_environment_variables(original_path)
            if os.path.basename(expanded) == folder_name:
                return expanded

        return os.path.join(base_path, folder_name)

    def _restore_single_directory(self, source_path: str, target_path: str, name: str, overwrite: bool) -> tuple[int, int]:
        """
        Restore a single directory safely.

        Args:
            source_path: Source path in backup
            target_path: Target path to restore to
            name: Display name for logging
            overwrite: Whether to overwrite existing files

        Returns:
            Tuple of (copied_files, failed_files)
        """
        copied_files = 0
        skipped_files = 0
        failed_files = 0

        try:
            self._update_progress(f"Restoring files to: {target_path}")
            PathUtils.ensure_directory(target_path)

            for root, dirs, files in os.walk(source_path):
                rel_dir = os.path.relpath(root, source_path)
                dest_dir = target_path if rel_dir == '.' else os.path.join(target_path, rel_dir)
                PathUtils.ensure_directory(dest_dir)

                for f in files:
                    src_file = os.path.join(root, f)
                    dest_file = os.path.join(dest_dir, f)

                    if os.path.exists(dest_file) and not overwrite:
                        skipped_files += 1
                        continue

                    try:
                        shutil.copy2(src_file, dest_file)
                        copied_files += 1
                    except Exception as fe:
                        self.logger.warning(f"Could not copy file {src_file} -> {dest_file}: {fe}")
                        failed_files += 1

            if failed_files > 0:
                self.logger.warning(f"⚠️ {failed_files} file(s) failed during restore of {name}. Run as Administrator if writing to Program Files.")
                self._update_progress(f"⚠️ {failed_files} file(s) failed (Administrator rights required)")

            self.logger.info(f"✓ Restored {name}: {copied_files} copied, {skipped_files} skipped, {failed_files} failed -> {target_path}")
            self._update_progress(f"✓ Restored {name} ({copied_files} files)")

        except Exception as e:
            self.logger.error(f"Failed to restore {name}: {e}")
            self._update_progress(f"Error restoring {name}: {e}")

        return (copied_files, failed_files)



    def _restore_flat_structure(self, backup_source: str, original_paths: List[str], category: str, overwrite: bool) -> None:
        """
        Fallback: Restore from old flat structure (backward compatibility)
        """
        try:
            backed_up_items = [d for d in os.listdir(backup_source) 
                              if os.path.isdir(os.path.join(backup_source, d))]
        except Exception as e:
            self.logger.error(f"Error reading backup source: {e}")
            return

        for item_name in backed_up_items:
            item_path = os.path.join(backup_source, item_name)

            # Find matching original path
            target_path = self._find_target_path(item_name, original_paths)

            if not target_path:
                self.logger.warning(f"Could not determine target for: {item_name}")
                continue

            # Expand environment variables
            expanded_target = PathUtils.expand_environment_variables(target_path)

            self._restore_single_directory(item_path, expanded_target, item_name, overwrite)

    def _restore_custom_locations(self, manifest: Dict, backup_dir: str, overwrite: bool) -> None:

        # Restore custom locations (non-standard paths like D:\GameLoop)
        
        custom_paths = manifest.get('source_paths', {}).get('custom_locations', [])

        if not custom_paths:
            return

        custom_backup = os.path.join(backup_dir, "CustomLocations")

        if not os.path.exists(custom_backup):
            return

        self._update_progress("Restoring custom locations...")

        try:
            for item in os.listdir(custom_backup):
                item_path = os.path.join(custom_backup, item)

                if not os.path.isdir(item_path):
                    continue

                # Find original path
                target_path = self._find_restore_target(item, custom_paths, "")

                if target_path:
                    self._restore_single_directory(item_path, target_path, item, overwrite)

        except Exception as e:
            self.logger.error(f"Error restoring custom locations: {e}")

    def _find_target_path(self, dir_name: str, original_paths: List[str]) -> Optional[str]:
        """
        Find target restoration path for backed up directory
        
        Args:
            dir_name: Name of backed up directory
            original_paths: List of original source paths
            
        Returns:
            Target path or None
        """
        for path in original_paths:
            expanded = PathUtils.expand_environment_variables(path)
            if os.path.basename(expanded) == dir_name:
                return path
        
        # If no exact match, return first path (fallback)
        return original_paths[0] if original_paths else None
    
    def _restore_registry(self, registry_files: List[str], backup_source: str) -> None:
        """
        Restore registry keys from backup
        
        Args:
            registry_files: List of registry file names
            backup_source: Backup registry directory
        """
        if not registry_files:
            self.logger.info("No registry keys to restore")
            return
        
        if not os.path.exists(backup_source):
            self.logger.warning(f"Registry backup not found: {backup_source}")
            return
        
        # Build full paths to registry files
        reg_file_paths = [os.path.join(backup_source, f) for f in registry_files]
        
        # Filter existing files
        existing_files = [f for f in reg_file_paths if os.path.exists(f)]
        
        if not existing_files:
            self.logger.warning("No registry files found to import")
            return
        
        self._update_progress("Importing registry keys...")
        imported_count = self.registry_manager.import_registry_files(existing_files)
        
        self._update_progress(f"Imported {imported_count} registry keys")
    
    def _restore_shortcuts(self, shortcuts_dir: str) -> None:
        """
        Restore Start Menu and Desktop shortcuts from backup.
        These are essential for Windows to show the app in Start Menu/Search.
        
        Args:
            shortcuts_dir: Path to the Shortcuts directory in the backup
        """
        if not os.path.exists(shortcuts_dir):
            self.logger.info("No shortcuts to restore")
            return
        
        import json
        
        # Load shortcut metadata
        metadata_path = os.path.join(shortcuts_dir, "_shortcut_metadata.json")
        if not os.path.exists(metadata_path):
            self.logger.warning("No shortcut metadata found, skipping shortcut restore")
            return
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                shortcut_metadata = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load shortcut metadata: {e}")
            return
        
        self._update_progress(f"Restoring {len(shortcut_metadata)} shortcuts...")
        
        restored_count = 0
        for entry in shortcut_metadata:
            name = entry.get('name')
            original_path = entry.get('original_path')
            is_directory = entry.get('is_directory', False)
            
            if not name or not original_path:
                continue
            
            source_in_backup = os.path.join(shortcuts_dir, name)
            
            if not os.path.exists(source_in_backup):
                self.logger.warning(f"Shortcut not found in backup: {name}")
                continue
            
            try:
                # Ensure parent directory exists
                parent_dir = os.path.dirname(original_path)
                PathUtils.ensure_directory(parent_dir)
                
                if is_directory:
                    if os.path.exists(original_path):
                        shutil.rmtree(original_path)
                    shutil.copytree(source_in_backup, original_path)
                    self._update_progress(f"Restored shortcut folder: {name}")
                else:
                    shutil.copy2(source_in_backup, original_path)
                    self._update_progress(f"Restored shortcut: {name}")
                
                restored_count += 1
                self.logger.info(f"✓ Restored shortcut: {source_in_backup} -> {original_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to restore shortcut {name}: {e}")
        
        self._update_progress(f"Restored {restored_count} shortcuts")
