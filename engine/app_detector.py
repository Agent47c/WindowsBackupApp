"""
Application Detector Module
Detects installed applications on Windows using registry
"""

import winreg
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from utils.logger import Logger


@dataclass
class InstalledApplication:
    """Represents an installed application"""
    name: str
    display_name: str
    install_location: Optional[str]
    publisher: Optional[str]
    version: Optional[str]
    registry_key: str
    uninstall_string: Optional[str] = None
    quiet_uninstall_string: Optional[str] = None
    modify_path: Optional[str] = None
    install_date: Optional[str] = None
    estimated_size: Optional[int] = None  # in KB
    is_system_component: bool = False
    windows_installer: bool = False
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, InstalledApplication):
            return self.name == other.name
        return False
    
    @property
    def size_display(self) -> str:
        """Human-readable size string"""
        if not self.estimated_size:
            return "Unknown"
        kb = self.estimated_size
        if kb < 1024:
            return f"{kb} KB"
        elif kb < 1024 * 1024:
            return f"{kb / 1024:.1f} MB"
        else:
            return f"{kb / (1024 * 1024):.2f} GB"
    
    @property
    def can_uninstall(self) -> bool:
        """Whether this app has an uninstall command"""
        return bool(self.uninstall_string)
    
    @property
    def can_silent_uninstall(self) -> bool:
        """Whether this app supports silent uninstall"""
        return bool(self.quiet_uninstall_string)


class ApplicationDetector:
    """Detects installed applications on Windows"""
    
    # Registry paths to check for installed applications
    REGISTRY_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    
    # Applications to exclude (Windows components, system tools)
    EXCLUDED_KEYWORDS = [
        'Microsoft Visual C++',
        'Microsoft .NET',
        'Update for',
        'Security Update',
        'Hotfix',
        'KB',
        'Windows',
        'Intel',
        'AMD',
        'NVIDIA',
        'Realtek',
        'Driver',
    ]
    
    def __init__(self):
        """Initialize Application Detector"""
        self.logger = Logger()
        self.applications: Dict[str, InstalledApplication] = {}
    
    def scan_installed_applications(self) -> List[InstalledApplication]:
        """
        Scan Windows registry for installed applications
        
        Returns:
            List of detected applications
        """
        self.logger.info("Scanning for installed applications...")
        self.applications.clear()
        
        for hkey, subkey_path in self.REGISTRY_PATHS:
            self._scan_registry_path(hkey, subkey_path)
        
        # Convert to sorted list
        app_list = sorted(self.applications.values(), key=lambda x: x.display_name.lower())
        
        self.logger.info(f"Found {len(app_list)} installed applications")
        return app_list
    
    def _scan_registry_path(self, hkey: int, subkey_path: str) -> None:
        """
        Scan a specific registry path for applications
        
        Args:
            hkey: Registry hive key
            subkey_path: Registry subkey path
        """
        try:
            with winreg.OpenKey(hkey, subkey_path) as key:
                index = 0
                while True:
                    try:
                        # Enumerate subkeys
                        subkey_name = winreg.EnumKey(key, index)
                        index += 1
                        
                        # Read application info from subkey
                        app = self._read_application_info(hkey, subkey_path, subkey_name)
                        
                        if app and self._is_valid_application(app):
                            self.applications[app.name] = app
                            
                    except OSError:
                        # No more subkeys
                        break
                        
        except FileNotFoundError:
            self.logger.debug(f"Registry path not found: {subkey_path}")
        except Exception as e:
            self.logger.error(f"Error scanning registry: {e}")
    
    def _read_application_info(
        self, 
        hkey: int, 
        subkey_path: str, 
        subkey_name: str
    ) -> Optional[InstalledApplication]:
        """
        Read application information from registry subkey
        
        Args:
            hkey: Registry hive key
            subkey_path: Registry subkey path
            subkey_name: Subkey name
            
        Returns:
            InstalledApplication or None
        """
        full_path = f"{subkey_path}\\{subkey_name}"
        
        try:
            with winreg.OpenKey(hkey, full_path) as app_key:
                # Read display name
                try:
                    display_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                except FileNotFoundError:
                    return None
                
                # Skip if no display name
                if not display_name or not isinstance(display_name, str):
                    return None
                
                # Read core info
                install_location = self._read_registry_value(app_key, "InstallLocation")
                publisher = self._read_registry_value(app_key, "Publisher")
                version = self._read_registry_value(app_key, "DisplayVersion")
                
                # Read uninstall info
                uninstall_string = self._read_registry_value(app_key, "UninstallString")
                quiet_uninstall_string = self._read_registry_value(app_key, "QuietUninstallString")
                modify_path = self._read_registry_value(app_key, "ModifyPath")
                install_date = self._read_registry_value(app_key, "InstallDate")
                
                # Read estimated size (integer value)
                estimated_size = self._read_registry_int(app_key, "EstimatedSize")
                
                # Read system component flag
                system_component = self._read_registry_int(app_key, "SystemComponent")
                is_system_component = (system_component == 1) if system_component is not None else False
                
                # Read Windows Installer flag
                win_installer = self._read_registry_int(app_key, "WindowsInstaller")
                windows_installer = (win_installer == 1) if win_installer is not None else False
                
                # Create registry key string
                hkey_name = "HKEY_LOCAL_MACHINE" if hkey == winreg.HKEY_LOCAL_MACHINE else "HKEY_CURRENT_USER"
                registry_key = f"{hkey_name}\\{full_path}"
                
                return InstalledApplication(
                    name=display_name,
                    display_name=display_name,
                    install_location=install_location,
                    publisher=publisher,
                    version=version,
                    registry_key=registry_key,
                    uninstall_string=uninstall_string,
                    quiet_uninstall_string=quiet_uninstall_string,
                    modify_path=modify_path,
                    install_date=install_date,
                    estimated_size=estimated_size,
                    is_system_component=is_system_component,
                    windows_installer=windows_installer
                )
                
        except Exception as e:
            self.logger.debug(f"Could not read app info from {subkey_name}: {e}")
            return None
    
    def _read_registry_value(self, key, value_name: str) -> Optional[str]:
        """
        Safely read a registry string value
        
        Args:
            key: Open registry key
            value_name: Value name to read
            
        Returns:
            Value as string or None
        """
        try:
            value = winreg.QueryValueEx(key, value_name)[0]
            return str(value) if value else None
        except (FileNotFoundError, OSError):
            return None
    
    def _read_registry_int(self, key, value_name: str) -> Optional[int]:
        """
        Safely read a registry integer value
        
        Args:
            key: Open registry key
            value_name: Value name to read
            
        Returns:
            Value as int or None
        """
        try:
            value, reg_type = winreg.QueryValueEx(key, value_name)
            return int(value) if value is not None else None
        except (FileNotFoundError, OSError, ValueError):
            return None
    
    def _is_valid_application(self, app: InstalledApplication) -> bool:
        """
        Check if application should be included in the list
        
        Args:
            app: Application to check
            
        Returns:
            True if valid user application
        """
        # Skip system components
        if app.is_system_component:
            return False
        
        # Check for excluded keywords
        for keyword in self.EXCLUDED_KEYWORDS:
            if keyword.lower() in app.display_name.lower():
                return False
        
        # Must have a display name
        if not app.display_name or len(app.display_name.strip()) < 2:
            return False
        
        return True
    
    def get_application_data_paths(self, app: InstalledApplication) -> Dict[str, List[str]]:
        """
        Comprehensive scan for application data across ALL possible locations

        Args:
            app: Installed application

        Returns:
            Dictionary with 'program_data' and 'user_data' paths
        """
        app_name = app.display_name
        publisher = app.publisher or ""
        install_location = app.install_location

        paths = {
            'program_data': [],
            'user_data': [],
            'registry_keys': [],
            'custom_locations': [],  # For non-standard locations
            'shortcuts': []  # Start Menu and Desktop shortcuts
        }

        self.logger.info(f"=== Comprehensive Scan for: {app_name} ===")

        # Generate name variations
        name_variations = self._generate_name_variations(app_name, publisher)
        self.logger.info(f"Name variations: {name_variations[:5]}...")  # Show first 5

        # Extract clean publisher name for publisher-based scanning
        publisher_names = self._extract_publisher_names(publisher)

        # PHASE 1: Standard Windows Locations across all available drives
        self._scan_standard_locations(name_variations, paths)

        # PHASE 2: Install Location & Uninstall Path extraction
        target_install_locations = []
        if install_location and os.path.exists(install_location):
            target_install_locations.append(install_location)

        for uninst in [app.uninstall_string, app.quiet_uninstall_string, app.modify_path]:
            extracted = self._extract_path_from_uninstall_string(uninst)
            if extracted and extracted not in target_install_locations:
                target_install_locations.append(extracted)
                self.logger.info(f"✓ Extracted installation directory from uninstall path: {extracted}")

        for loc in target_install_locations:
            self._scan_install_location(loc, paths)


        # PHASE 2.5: Publisher-based folder scanning
        # For apps like Adobe Photoshop, scan all "Adobe" folders everywhere
        if publisher_names:
            self._scan_publisher_folders(publisher_names, name_variations, paths)

        # PHASE 3: Registry-based Discovery (find paths from registry)
        registry_paths = self._discover_paths_from_registry(name_variations)
        self._process_registry_discovered_paths(registry_paths, paths)

        # PHASE 4: All Drives Scan (if nothing found in C:)
        if not paths['program_data'] and not paths['user_data']:
            self.logger.info("No paths found in standard locations, scanning all drives...")
            self._scan_all_drives(name_variations, paths)

        # PHASE 5: Package Manager Locations
        self._scan_package_managers(name_variations, paths)

        # PHASE 6: Find Registry Keys
        paths['registry_keys'] = self._find_registry_keys_comprehensive(name_variations)

        # PHASE 6.5: Find Shell Extension / Context Menu registry keys
        shell_keys = self._find_shell_extension_keys(name_variations)
        paths['registry_keys'].extend(shell_keys)

        # PHASE 7: Add the app's OWN Uninstall registry entry
        # This is CRITICAL — without this, Windows won't recognize the app after restore
        if app.registry_key and app.registry_key not in paths['registry_keys']:
            paths['registry_keys'].append(app.registry_key)
            self.logger.info(f"✓ Added Uninstall registry key: {app.registry_key}")

        # PHASE 8: Find Start Menu and Desktop shortcuts
        all_names = name_variations + publisher_names
        paths['shortcuts'] = self._find_shortcuts(all_names)

        # Clean up and deduplicate
        paths = self._cleanup_paths(paths)

        self.logger.info(f"=== SCAN COMPLETE ===")
        self.logger.info(f"Program Data: {len(paths['program_data'])} locations")
        self.logger.info(f"User Data: {len(paths['user_data'])} locations")
        self.logger.info(f"Custom Locations: {len(paths['custom_locations'])} locations")
        self.logger.info(f"Registry Keys: {len(paths['registry_keys'])} keys")
        self.logger.info(f"Shortcuts: {len(paths['shortcuts'])} found")

        return paths

    def _generate_name_variations(self, app_name: str, publisher: str = "") -> List[str]:
        """Generate extensive name variations"""
        import re

        variations = set()

        # Original name
        variations.add(app_name)

        # Remove version numbers (e.g., "MSI Afterburner 4.6.6" -> "MSI Afterburner")
        name_no_version = re.sub(r'\s+\d+(\.\d+)*$', '', app_name).strip()
        name_no_version = re.sub(r'\s+v?\d+(\.\d+)*', '', name_no_version).strip()
        variations.add(name_no_version)

        # Remove common suffixes
        for suffix in [' (x64)', ' (x86)', ' (64-bit)', ' (32-bit)', ' Desktop', 
                       ' App', ' Application', ' Client', ' Player']:
            clean = app_name.replace(suffix, '').strip()
            variations.add(clean)
            variations.add(name_no_version.replace(suffix, '').strip())

        # First word (often company name)
        first_word = app_name.split()[0]
        if len(first_word) > 2:
            variations.add(first_word)

        # No spaces
        variations.add(app_name.replace(' ', ''))
        variations.add(name_no_version.replace(' ', ''))

        # Lowercase
        variations.add(app_name.lower())
        variations.add(name_no_version.lower())
        variations.add(app_name.lower().replace(' ', ''))

        # Hyphens and underscores
        variations.add(app_name.replace(' ', '-'))
        variations.add(name_no_version.replace(' ', '-'))
        variations.add(app_name.lower().replace(' ', '-'))
        variations.add(app_name.replace(' ', '_'))
        variations.add(name_no_version.replace(' ', '_'))

        # Dots instead of spaces
        variations.add(app_name.replace(' ', '.'))
        variations.add(name_no_version.replace(' ', '.'))

        # Publisher variations
        if publisher:
            pub_clean = publisher.split(',')[0].split(' Inc')[0].split(' LLC')[0].strip()
            variations.add(pub_clean)
            variations.add(pub_clean.replace(' ', ''))
            variations.add(pub_clean.lower())
            variations.add(pub_clean.lower().replace(' ', ''))
            
            # Publisher + App combinations (e.g., "Adobe.AfterEffects")
            simple_name = name_no_version.split()[-1] if name_no_version.split() else name_no_version
            variations.add(f"{pub_clean}.{simple_name}")
            variations.add(f"com.{pub_clean.lower()}.{simple_name.lower()}")

        # Reverse-domain names (e.g., com.adobe.dunamis)
        words = app_name.lower().split()
        if len(words) >= 2:
            variations.add(f"com.{words[0]}.{words[1]}")

        # Remove empty and short strings
        return [v for v in variations if v and len(v) > 1]

    def _get_available_drives(self) -> List[str]:
        """Get all active drive letters on Windows"""
        import string
        drives = ['C:\\']
        if os.name == 'nt':
            try:
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive_path = f"{letter}:\\"
                        if drive_path != 'C:\\' and os.path.exists(drive_path):
                            drives.append(drive_path)
                    bitmask >>= 1
            except Exception:
                pass
        return drives

    def _extract_path_from_uninstall_string(self, uninst_str: Optional[str]) -> Optional[str]:
        """
        Extract directory path from an uninstall string or command.
        Example: '"D:\\Program Files\\txgameassistant\\uninstall.exe" -uninstall'
                 -> 'D:\\Program Files\\txgameassistant'
        """
        if not uninst_str or not isinstance(uninst_str, str):
            return None

        import re
        # Find executable path pattern
        match = re.search(r'["\']?([A-Za-z]:\\[^"\'\:]+?\.(?:exe|bat|cmd|msi))', uninst_str, re.IGNORECASE)
        if match:
            exe_path = match.group(1)
            dir_path = os.path.dirname(exe_path)
            if os.path.exists(dir_path) and len(dir_path) > 3:
                return os.path.abspath(dir_path)

        clean_str = uninst_str.strip('"\' ')
        if os.path.exists(clean_str):
            if os.path.isfile(clean_str):
                return os.path.abspath(os.path.dirname(clean_str))
            return os.path.abspath(clean_str)

        return None

    def _scan_standard_locations(self, name_variations: List[str], paths: Dict) -> None:
        """Scan all standard Windows locations across all available drives"""
        program_data_locs = [
            os.path.expandvars('%ProgramFiles%'),
            os.path.expandvars('%ProgramFiles(x86)%'),
            os.path.join(os.path.expandvars('%ProgramFiles%'), 'Common Files'),
            os.path.join(os.path.expandvars('%ProgramFiles(x86)%'), 'Common Files'),
            os.path.expandvars('%ProgramData%'),
        ]

        # Dynamically add locations on secondary drives (D:\, E:\, etc.)
        for drive in self._get_available_drives():
            if drive.upper() != 'C:\\':
                program_data_locs.extend([
                    os.path.join(drive, 'Program Files'),
                    os.path.join(drive, 'Program Files (x86)'),
                    os.path.join(drive, 'ProgramData'),
                    os.path.join(drive, 'Games'),
                ])

        locations = {
            'program_data': program_data_locs,
            'user_data': [
                os.path.expandvars('%APPDATA%'),           # Roaming
                os.path.expandvars('%LOCALAPPDATA%'),      # Local
                os.path.join(os.path.expandvars('%USERPROFILE%'), 'AppData', 'LocalLow'),  # LocalLow
                os.path.join(os.path.expandvars('%USERPROFILE%'), 'Documents'),            # Documents
                os.path.join('C:\\', 'Users', 'Public', 'Documents'),                      # Public Documents
                os.path.expandvars('%USERPROFILE%'),       # User home
            ]
        }

        for category, base_dirs in locations.items():
            for base_dir in base_dirs:
                if not os.path.exists(base_dir):
                    continue

                for name_var in name_variations:
                    check_path = os.path.join(base_dir, name_var)
                    if os.path.exists(check_path) and self._has_content(check_path):
                        if check_path not in paths[category]:
                            paths[category].append(check_path)
                            self.logger.info(f"✓ Found {category}: {check_path}")

    def _scan_install_location(self, install_location: str, paths: Dict) -> None:
        """Scan and include full install location and its config/data folders"""
        if not install_location or not os.path.exists(install_location):
            return

        clean_path = os.path.abspath(install_location)
        if os.path.isfile(clean_path):
            clean_path = os.path.dirname(clean_path)

        self.logger.info(f"Scanning install location: {clean_path}")
        path_lower = clean_path.lower()

        # Always include the entire installation directory so all files are backed up
        if any(x in path_lower for x in ['program files', 'programdata']):
            if clean_path not in paths['program_data']:
                paths['program_data'].append(clean_path)
                self.logger.info(f"✓ Added full installation folder: {clean_path}")
        elif any(x in path_lower for x in ['appdata', 'users']):
            if clean_path not in paths['user_data']:
                paths['user_data'].append(clean_path)
                self.logger.info(f"✓ Added full installation folder: {clean_path}")
        else:
            # Custom drive or folder (e.g. D:\Program Files\txgameassistant or D:\Games)
            if clean_path not in paths['custom_locations']:
                paths['custom_locations'].append(clean_path)
                self.logger.info(f"✓ Added custom installation folder: {clean_path}")

        # Check subfolders
        config_folders = ['config', 'configs', 'data', 'settings', 'profiles', 
                         'saves', 'plugins', 'addons', 'mods', 'userdata', 'ui', 'res']

        for folder in config_folders:
            check_path = os.path.join(clean_path, folder)
            if os.path.exists(check_path) and self._has_content(check_path):
                if check_path not in paths['program_data'] and check_path not in paths['custom_locations']:
                    paths['program_data'].append(check_path)
                    self.logger.info(f"✓ Found subfolder in install location: {check_path}")


    def _discover_paths_from_registry(self, name_variations: List[str]) -> List[str]:
        """
        Search registry for installation/data paths
        Returns list of paths found in registry
        """
        import winreg

        discovered_paths = []

        # Registry locations to search for paths
        search_locations = [
            (winreg.HKEY_CURRENT_USER, r"Software"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node"),
        ]

        # Common registry value names that contain paths
        path_value_names = ['InstallPath', 'InstallDir', 'InstallLocation', 'Path', 
                            'DataPath', 'DataDir', 'ConfigPath', 'UserDataPath']

        for hkey, base_path in search_locations:
            for name_var in name_variations:
                key_path = f"{base_path}\\{name_var}"

                try:
                    with winreg.OpenKey(hkey, key_path) as key:
                        # Try to find path values
                        for value_name in path_value_names:
                            try:
                                path_value, _ = winreg.QueryValueEx(key, value_name)
                                if path_value and isinstance(path_value, str) and os.path.exists(path_value):
                                    discovered_paths.append(path_value)
                                    self.logger.info(f"✓ Registry path found: {path_value}")
                            except:
                                pass
                except:
                    pass

        return discovered_paths

    def _process_registry_discovered_paths(self, registry_paths: List[str], paths: Dict) -> None:
        """Process paths discovered from registry"""

        for path in registry_paths:
            if not os.path.exists(path):
                continue

            path_lower = path.lower()

            # Categorize based on location
            if any(x in path_lower for x in ['program files', 'programdata']):
                if path not in paths['program_data']:
                    paths['program_data'].append(path)
            elif any(x in path_lower for x in ['appdata', 'users']):
                if path not in paths['user_data']:
                    paths['user_data'].append(path)
            else:
                # Custom location (not in C:\)
                if path not in paths['custom_locations']:
                    paths['custom_locations'].append(path)

    def _scan_all_drives(self, name_variations: List[str], paths: Dict) -> None:
        """
        Scan all available drives for application data
        This is used when nothing is found in C: drive
        """
        import string

        self.logger.info("Scanning all drives for application...")

        # Get all available drives
        available_drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                available_drives.append(drive)

        # Skip C: as it was already scanned
        available_drives = [d for d in available_drives if not d.startswith('C:')]

        for drive in available_drives:
            self.logger.info(f"Scanning drive: {drive}")

            # Common installation paths on other drives
            search_paths = [
                drive,  # Root
                os.path.join(drive, 'Program Files'),
                os.path.join(drive, 'Program Files (x86)'),
                os.path.join(drive, 'Games'),
                os.path.join(drive, 'Applications'),
            ]

            for base_path in search_paths:
                if not os.path.exists(base_path):
                    continue

                for name_var in name_variations:
                    check_path = os.path.join(base_path, name_var)
                    if os.path.exists(check_path) and self._has_content(check_path):
                        if check_path not in paths['custom_locations']:
                            paths['custom_locations'].append(check_path)
                            self.logger.info(f"✓ Found on {drive}: {check_path}")

    def _scan_package_managers(self, name_variations: List[str], paths: Dict) -> None:
        """
        Scan package manager locations (winget, chocolatey, scoop, etc.)
        """

        # WinGet packages location
        localappdata = os.path.expandvars('%LOCALAPPDATA%')
        winget_packages = os.path.join(localappdata, 'Microsoft', 'WinGet', 'Packages')

        if os.path.exists(winget_packages):
            try:
                for package in os.listdir(winget_packages):
                    for name_var in name_variations:
                        if name_var.lower() in package.lower():
                            package_path = os.path.join(winget_packages, package)
                            if self._has_content(package_path):
                                if package_path not in paths['user_data']:
                                    paths['user_data'].append(package_path)
                                    self.logger.info(f"✓ Found WinGet package: {package_path}")
            except:
                pass

        # Chocolatey location
        choco_path = os.path.join('C:\\', 'ProgramData', 'chocolatey', 'lib')
        if os.path.exists(choco_path):
            try:
                for package in os.listdir(choco_path):
                    for name_var in name_variations:
                        if name_var.lower() in package.lower():
                            package_path = os.path.join(choco_path, package)
                            if self._has_content(package_path):
                                if package_path not in paths['program_data']:
                                    paths['program_data'].append(package_path)
                                    self.logger.info(f"✓ Found Chocolatey package: {package_path}")
            except:
                pass

        # Scoop location
        scoop_path = os.path.join(os.path.expandvars('%USERPROFILE%'), 'scoop', 'apps')
        if os.path.exists(scoop_path):
            try:
                for package in os.listdir(scoop_path):
                    for name_var in name_variations:
                        if name_var.lower() in package.lower():
                            package_path = os.path.join(scoop_path, package)
                            if self._has_content(package_path):
                                if package_path not in paths['user_data']:
                                    paths['user_data'].append(package_path)
                                    self.logger.info(f"✓ Found Scoop package: {package_path}")
            except:
                pass

    def _find_registry_keys_comprehensive(self, name_variations: List[str]) -> List[str]:
        """Comprehensive registry key search"""
        import winreg

        found_keys = []

        search_locations = [
            (winreg.HKEY_CURRENT_USER, r"Software"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node"),
        ]

        for hkey, base_path in search_locations:
            for name_var in name_variations:
                key_path = f"{base_path}\\{name_var}"

                try:
                    with winreg.OpenKey(hkey, key_path) as key:
                        num_subkeys, num_values, _ = winreg.QueryInfoKey(key)
                        if num_subkeys > 0 or num_values > 0:
                            hkey_name = "HKEY_CURRENT_USER" if hkey == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
                            full_key = f"{hkey_name}\\{key_path}"
                            if full_key not in found_keys:
                                found_keys.append(full_key)
                                self.logger.info(f"✓ Found registry key: {full_key}")
                except:
                    pass

        return found_keys

    def _extract_publisher_names(self, publisher: str) -> List[str]:
        """
        Extract clean publisher names for folder scanning.
        E.g., 'Adobe Systems Incorporated' -> ['Adobe', 'Adobe Systems']
        """
        if not publisher:
            return []
        
        names = set()
        
        # Clean publisher string
        pub = publisher.split(',')[0].strip()
        for suffix in [' Inc', ' LLC', ' Ltd', ' Corp', ' Corporation', 
                       ' Incorporated', ' Software', ' Systems', ' Co.', ' GmbH']:
            pub = pub.replace(suffix, '').strip()
        
        if pub and len(pub) > 1:
            names.add(pub)
            # First word (usually the key brand name)
            first = pub.split()[0]
            if len(first) > 2:
                names.add(first)
        
        return list(names)

    def _scan_publisher_folders(self, publisher_names: List[str], 
                                 name_variations: List[str],
                                 paths: Dict) -> None:
        r"""
        Scan for publisher-named folders across all standard locations.
        For apps like Adobe Photoshop, finds C:\Program Files\Adobe\Photoshop\
        and all related data under the publisher umbrella.
        """
        # All locations to scan for publisher folders
        scan_locations = {
            'program_data': [
                os.path.expandvars('%ProgramFiles%'),
                os.path.expandvars('%ProgramFiles(x86)%'),
                os.path.expandvars('%ProgramData%'),
            ],
            'user_data': [
                os.path.expandvars('%APPDATA%'),
                os.path.expandvars('%LOCALAPPDATA%'),
                os.path.join(os.path.expandvars('%USERPROFILE%'), 'AppData', 'LocalLow'),
                os.path.join(os.path.expandvars('%USERPROFILE%'), 'Documents'),
                os.path.join('C:\\', 'Users', 'Public', 'Documents'),
            ]
        }

        
        # Add secondary drives for publisher folder scanning
        for drive in self._get_available_drives():
            if drive.upper() != 'C:\\':
                scan_locations['program_data'].extend([
                    os.path.join(drive, 'Program Files'),
                    os.path.join(drive, 'Program Files (x86)'),
                    os.path.join(drive, 'ProgramData'),
                ])

        for category, base_dirs in scan_locations.items():
            for base_dir in base_dirs:
                if not os.path.exists(base_dir):
                    continue
                
                for pub_name in publisher_names:
                    pub_folder = os.path.join(base_dir, pub_name)
                    
                    if not os.path.exists(pub_folder) or not os.path.isdir(pub_folder):
                        continue
                    
                    self.logger.info(f"✓ Found Publisher Umbrella directory: {pub_folder}")
                    
                    try:
                        sub_items = os.listdir(pub_folder)
                    except Exception:
                        continue
                    
                    # Check if any sub-folder matches the app name
                    has_app_subfolder = False
                    for sub_item in sub_items:
                        sub_path = os.path.join(pub_folder, sub_item)
                        if not os.path.isdir(sub_path):
                            continue
                        
                        sub_lower = sub_item.lower()
                        for name_var in name_variations:
                            if name_var.lower() in sub_lower or sub_lower in name_var.lower():
                                if sub_path not in paths[category]:
                                    paths[category].append(sub_path)
                                    self.logger.info(f"  ✓ Publisher sub-folder: {sub_path}")
                                has_app_subfolder = True
                                break
                    
                    # Always include publisher umbrella folder so shared components are backed up
                    if has_app_subfolder or self._has_content(pub_folder):
                        if pub_folder not in paths[category] and pub_folder not in paths['custom_locations']:
                            paths[category].append(pub_folder)
                            self.logger.info(f"  ✓ Publisher umbrella parent folder: {pub_folder}")


    def _find_shell_extension_keys(self, name_variations: List[str]) -> List[str]:
        """
        Find shell extension / context menu handler registry keys.
        Apps like 7-Zip register context menu entries here.
        """
        import winreg
        found_keys = []
        
        # Context menu handler locations
        handler_paths = [
            r"*\shellex\ContextMenuHandlers",
            r"Directory\shellex\ContextMenuHandlers",
            r"Directory\Background\shellex\ContextMenuHandlers",
            r"Folder\shellex\ContextMenuHandlers",
            r"Drive\shellex\ContextMenuHandlers",
        ]
        
        for handler_path in handler_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, handler_path) as parent_key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(parent_key, i)
                            subkey_lower = subkey_name.lower()
                            
                            # Check if this handler matches any app name variation
                            for name_var in name_variations:
                                if name_var.lower() in subkey_lower or subkey_lower in name_var.lower():
                                    full_key = f"HKEY_CLASSES_ROOT\\{handler_path}\\{subkey_name}"
                                    if full_key not in found_keys:
                                        found_keys.append(full_key)
                                        self.logger.info(f"✓ Found shell extension: {full_key}")
                                    break
                            
                            i += 1
                        except OSError:
                            break
            except Exception:
                pass
        
        # Also check for file type associations registered by the app
        # Look in HKCR for keys matching app name under CLSID
        try:
            clsid_path = r"CLSID"
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, clsid_path) as clsid_key:
                i = 0
                checked = 0
                while checked < 200:  # Limit to prevent scanning thousands of CLSIDs
                    try:
                        subkey_name = winreg.EnumKey(clsid_key, i)
                        i += 1
                        
                        # Read the default value of this CLSID to check app name
                        try:
                            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 
                                              f"{clsid_path}\\{subkey_name}") as sub:
                                default_val = winreg.QueryValue(sub, None)
                                if default_val:
                                    for name_var in name_variations:
                                        if name_var.lower() in default_val.lower():
                                            full_key = f"HKEY_CLASSES_ROOT\\{clsid_path}\\{subkey_name}"
                                            if full_key not in found_keys:
                                                found_keys.append(full_key)
                                                self.logger.info(f"✓ Found CLSID: {full_key} ({default_val})")
                                            break
                        except Exception:
                            pass
                        
                        checked += 1
                    except OSError:
                        break
        except Exception:
            pass
        
        return found_keys

    def _has_content(self, path: str) -> bool:
        """Check if path has actual content"""
        try:
            if not os.path.exists(path):
                return False
            if os.path.isfile(path):
                return os.path.getsize(path) > 0
            if os.path.isdir(path):
                return len(os.listdir(path)) > 0
            return False
        except:
            return False

    def _has_config_files(self, directory: str) -> bool:
        """Check if directory contains configuration files"""
        config_extensions = ['.ini', '.cfg', '.conf', '.config', '.xml', '.json', 
                            '.yaml', '.yml', '.toml', '.properties', '.dat']

        try:
            for item in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, item)):
                    _, ext = os.path.splitext(item.lower())
                    if ext in config_extensions:
                        return True
            return False
        except:
            return False

    def _cleanup_paths(self, paths: Dict) -> Dict:
        """Remove duplicates and normalize paths"""

        for category in ['program_data', 'user_data', 'custom_locations']:
            if category in paths:
                # Normalize and deduplicate
                seen = set()
                unique = []
                for path in paths[category]:
                    normalized = os.path.normpath(path).lower()
                    if normalized not in seen:
                        seen.add(normalized)
                        unique.append(path)
                paths[category] = unique

        # Remove duplicate registry keys
        if 'registry_keys' in paths:
            paths['registry_keys'] = list(set(paths['registry_keys']))

        return paths

    def _find_shortcuts(self, name_variations: List[str]) -> List[str]:
        """
        Find Start Menu and Desktop shortcuts (.lnk files) for the application.
        These are essential for Windows to show the app in search and Start Menu.

        Returns:
            List of shortcut file/folder paths
        """
        found_shortcuts = []

        # Locations to search for shortcuts
        shortcut_locations = [
            # All-users Start Menu
            os.path.join(os.path.expandvars('%ProgramData%'), 
                        'Microsoft', 'Windows', 'Start Menu', 'Programs'),
            # Current-user Start Menu 
            os.path.join(os.path.expandvars('%APPDATA%'), 
                        'Microsoft', 'Windows', 'Start Menu', 'Programs'),
            # Public Desktop
            os.path.join('C:\\', 'Users', 'Public', 'Desktop'),
            # User Desktop
            os.path.join(os.path.expandvars('%USERPROFILE%'), 'Desktop'),
        ]

        for location in shortcut_locations:
            if not os.path.exists(location):
                continue

            try:
                # Check for matching folders (e.g., "MSI Afterburner" folder in Start Menu)
                for item in os.listdir(location):
                    item_path = os.path.join(location, item)
                    item_lower = item.lower()

                    for name_var in name_variations:
                        if name_var.lower() in item_lower:
                            if item_path not in found_shortcuts:
                                found_shortcuts.append(item_path)
                                self.logger.info(f"✓ Found shortcut: {item_path}")
                            break

                    # Also check .lnk files directly
                    if os.path.isfile(item_path) and item_lower.endswith('.lnk'):
                        # Already checked by name above, but also check
                        # .lnk target if needed in the future
                        pass

            except Exception as e:
                self.logger.debug(f"Error scanning shortcuts in {location}: {e}")

        return found_shortcuts