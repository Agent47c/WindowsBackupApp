"""
Uninstall Engine Module
Handles application uninstallation, verification, and cleanup
"""

import subprocess
import os
import shutil
import time
import shlex
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from engine.app_detector import InstalledApplication, ApplicationDetector
from utils.logger import Logger
from utils.path_utils import PathUtils


class UninstallEngine:
    """Handles application uninstall operations"""
    
    def __init__(self):
        """Initialize Uninstall Engine"""
        self.logger = Logger()
        self.app_detector = ApplicationDetector()
        self.progress_callback: Optional[Callable[[str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback function for progress updates"""
        self.progress_callback = callback
    
    def _update_progress(self, message: str) -> None:
        """Send progress update to callback"""
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def get_uninstall_info(self, app: InstalledApplication) -> Dict:
        """
        Get detailed information about what uninstalling will do
        
        Args:
            app: Application to get info for
            
        Returns:
            Dictionary with uninstall details
        """
        info = {
            'app_name': app.display_name,
            'can_uninstall': app.can_uninstall,
            'can_silent_uninstall': app.can_silent_uninstall,
            'uninstall_command': app.uninstall_string,
            'silent_command': app.quiet_uninstall_string,
            'install_location': app.install_location,
            'estimated_size': app.size_display,
            'uses_msi': app.windows_installer,
        }
        
        # Detect known data locations
        data_paths = self.app_detector.get_application_data_paths(app)
        info['data_locations'] = data_paths
        info['has_leftover_data'] = bool(
            data_paths.get('user_data') or 
            data_paths.get('program_data') or 
            data_paths.get('custom_locations')
        )
        
        return info
    
    def _parse_uninstall_string(self, uninstall_string: str) -> Tuple[str, List[str]]:
        """
        Parse an UninstallString into executable and arguments
        
        Handles formats like:
        - "C:\\path\\uninst.exe"
        - C:\\path\\uninst.exe /S
        - "C:\\path\\uninst.exe" --uninstall
        - MsiExec.exe /I{GUID}
        - MsiExec.exe /X{GUID}
        
        Args:
            uninstall_string: Raw uninstall string from registry
            
        Returns:
            Tuple of (executable_path, arguments_list)
        """
        uninstall_string = uninstall_string.strip()
        
        # Handle MsiExec specially
        if uninstall_string.lower().startswith('msiexec'):
            parts = uninstall_string.split(None, 1)
            exe = parts[0]
            args = parts[1].split() if len(parts) > 1 else []
            return exe, args
        
        # Handle quoted path
        if uninstall_string.startswith('"'):
            # Find closing quote
            end_quote = uninstall_string.find('"', 1)
            if end_quote != -1:
                exe = uninstall_string[1:end_quote]
                remaining = uninstall_string[end_quote + 1:].strip()
                args = remaining.split() if remaining else []
                return exe, args
        
        # Handle unquoted path - try to find the .exe
        lower = uninstall_string.lower()
        exe_pos = lower.find('.exe')
        if exe_pos != -1:
            exe = uninstall_string[:exe_pos + 4]
            remaining = uninstall_string[exe_pos + 4:].strip()
            args = remaining.split() if remaining else []
            return exe, args
        
        # Fallback: first token is executable
        parts = uninstall_string.split(None, 1)
        exe = parts[0]
        args = parts[1].split() if len(parts) > 1 else []
        return exe, args
    
    def uninstall_application(
        self,
        app: InstalledApplication,
        silent: bool = False,
        timeout: int = 300
    ) -> Dict:
        """
        Uninstall an application
        
        Args:
            app: Application to uninstall
            silent: Whether to attempt silent uninstall
            timeout: Maximum seconds to wait for uninstaller
            
        Returns:
            Dictionary with result details:
            - success: bool
            - message: str
            - leftover_paths: list of paths that still exist
        """
        result = {
            'success': False,
            'message': '',
            'leftover_paths': [],
            'returncode': None
        }
        
        # Determine which uninstall command to use
        if silent and app.quiet_uninstall_string:
            uninstall_cmd = app.quiet_uninstall_string
            self._update_progress(f"Using silent uninstall for: {app.display_name}")
        elif app.uninstall_string:
            uninstall_cmd = app.uninstall_string
            self._update_progress(f"Using standard uninstall for: {app.display_name}")
        else:
            result['message'] = f"No uninstall command found for {app.display_name}"
            self._update_progress(result['message'])
            return result
        
        self._update_progress(f"Uninstall command: {uninstall_cmd}")
        
        try:
            # Parse the uninstall string
            exe, args = self._parse_uninstall_string(uninstall_cmd)
            
            # For MSI-based uninstalls, add /quiet flag for silent mode
            if silent and exe.lower().startswith('msiexec'):
                # Replace /I with /X for uninstall, add /quiet
                args = [a.replace('/I', '/X') for a in args]
                if '/quiet' not in args and '/qn' not in args:
                    args.append('/quiet')
                    args.append('/norestart')
            
            # Build command
            cmd = [exe] + args
            self._update_progress(f"Executing: {' '.join(cmd)}")
            
            # Run the uninstaller
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            result['returncode'] = process.returncode
            
            if process.returncode == 0:
                self._update_progress(f"Uninstaller exited with code 0 (success)")
            else:
                self._update_progress(
                    f"Uninstaller exited with code {process.returncode}"
                )
                if process.stderr:
                    self._update_progress(f"Stderr: {process.stderr[:500]}")
            
            # Wait a moment for uninstaller to finish cleanup
            time.sleep(2)
            
            # Verify uninstallation
            verification = self.verify_uninstall(app)
            
            if verification['registry_removed']:
                result['success'] = True
                result['message'] = f"Successfully uninstalled {app.display_name}"
                result['leftover_paths'] = verification['leftover_paths']
                
                if verification['leftover_paths']:
                    self._update_progress(
                        f"Uninstalled but {len(verification['leftover_paths'])} "
                        f"leftover locations remain"
                    )
            else:
                # Registry entry still exists - might need user interaction
                if process.returncode == 0:
                    result['success'] = True
                    result['message'] = (
                        f"Uninstaller completed but registry entry still exists. "
                        f"This may require a restart."
                    )
                else:
                    result['message'] = (
                        f"Uninstall may have failed (exit code: {process.returncode}). "
                        f"Registry entry still exists."
                    )
            
            self._update_progress(result['message'])
            return result
            
        except subprocess.TimeoutExpired:
            result['message'] = f"Uninstaller timed out after {timeout} seconds"
            self._update_progress(result['message'])
            return result
            
        except FileNotFoundError as e:
            result['message'] = f"Uninstaller not found: {e}"
            self._update_progress(result['message'])
            return result
            
        except Exception as e:
            result['message'] = f"Uninstall error: {e}"
            self.logger.error(f"Exception during uninstall: {e}")
            self._update_progress(result['message'])
            return result
    
    def verify_uninstall(self, app: InstalledApplication) -> Dict:
        """
        Verify whether an application has been uninstalled
        
        Args:
            app: Application to verify
            
        Returns:
            Dictionary with:
            - registry_removed: bool
            - install_location_removed: bool  
            - leftover_paths: list of remaining paths
        """
        verification = {
            'registry_removed': True,
            'install_location_removed': True,
            'leftover_paths': []
        }
        
        # Check if registry entry still exists
        try:
            reg_key = app.registry_key
            # Parse hive and path
            if reg_key.startswith("HKEY_LOCAL_MACHINE\\"):
                hive = winreg.HKEY_LOCAL_MACHINE
                key_path = reg_key[len("HKEY_LOCAL_MACHINE\\"):]
            elif reg_key.startswith("HKEY_CURRENT_USER\\"):
                hive = winreg.HKEY_CURRENT_USER
                key_path = reg_key[len("HKEY_CURRENT_USER\\"):]
            else:
                hive = None
                key_path = None
            
            if hive is not None and key_path:
                try:
                    with winreg.OpenKey(hive, key_path):
                        verification['registry_removed'] = False
                        self.logger.info(f"Registry entry still exists: {reg_key}")
                except FileNotFoundError:
                    verification['registry_removed'] = True
                    self.logger.info(f"Registry entry removed: {reg_key}")
        except Exception as e:
            self.logger.warning(f"Could not verify registry: {e}")
        
        # Check install location
        if app.install_location:
            if os.path.exists(app.install_location):
                verification['install_location_removed'] = False
                verification['leftover_paths'].append(app.install_location)
                self.logger.info(f"Install location still exists: {app.install_location}")
            else:
                self.logger.info(f"Install location removed: {app.install_location}")
        
        # Check common data locations
        data_paths = self.app_detector.get_application_data_paths(app)
        
        for category in ['user_data', 'program_data', 'custom_locations']:
            for path in data_paths.get(category, []):
                if os.path.exists(path):
                    verification['leftover_paths'].append(path)
        
        return verification
    
    def cleanup_leftover_data(
        self,
        app: InstalledApplication,
        paths_to_clean: List[str],
        clean_registry: bool = False
    ) -> Dict:
        """
        Clean up leftover data after uninstallation
        
        Args:
            app: The uninstalled application
            paths_to_clean: List of file/directory paths to remove
            clean_registry: Whether to also remove leftover registry keys
            
        Returns:
            Dictionary with cleanup results
        """
        results = {
            'files_removed': 0,
            'files_failed': 0,
            'registry_cleaned': False,
            'errors': []
        }
        
        # Clean file paths
        for path in paths_to_clean:
            try:
                if not os.path.exists(path):
                    continue
                
                # Safety check
                if not PathUtils.is_safe_path(path):
                    self._update_progress(f"Skipping unsafe path: {path}")
                    continue
                
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    self._update_progress(f"Removed directory: {path}")
                else:
                    os.remove(path)
                    self._update_progress(f"Removed file: {path}")
                
                results['files_removed'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to remove {path}: {e}")
                results['files_failed'] += 1
                results['errors'].append(f"{path}: {e}")
        
        # Clean registry keys
        if clean_registry:
            try:
                registry_keys = self.app_detector.get_application_data_paths(app).get('registry_keys', [])
                for key in registry_keys:
                    self._delete_registry_key(key)
                results['registry_cleaned'] = True
                self._update_progress("Cleaned leftover registry keys")
            except Exception as e:
                results['errors'].append(f"Registry cleanup: {e}")
        
        return results
    
    def _delete_registry_key(self, full_key_path: str) -> bool:
        """
        Delete a registry key
        
        Args:
            full_key_path: Full registry key path (e.g., HKEY_CURRENT_USER\\Software\\AppName)
            
        Returns:
            True if deleted successfully
        """
        try:
            if full_key_path.startswith("HKEY_LOCAL_MACHINE\\"):
                hive = winreg.HKEY_LOCAL_MACHINE
                key_path = full_key_path[len("HKEY_LOCAL_MACHINE\\"):]
            elif full_key_path.startswith("HKEY_CURRENT_USER\\"):
                hive = winreg.HKEY_CURRENT_USER
                key_path = full_key_path[len("HKEY_CURRENT_USER\\"):]
            else:
                return False
            
            # Split into parent and child
            parts = key_path.rsplit('\\', 1)
            if len(parts) == 2:
                parent_path, child_name = parts
                with winreg.OpenKey(hive, parent_path, 0, winreg.KEY_ALL_ACCESS) as parent_key:
                    winreg.DeleteKey(parent_key, child_name)
                    self.logger.info(f"Deleted registry key: {full_key_path}")
                    return True
            
        except FileNotFoundError:
            self.logger.info(f"Registry key already removed: {full_key_path}")
            return True
        except Exception as e:
            self.logger.warning(f"Could not delete registry key {full_key_path}: {e}")
            return False
