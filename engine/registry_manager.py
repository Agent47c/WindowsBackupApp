"""
Registry Manager Module
Handles Windows registry backup and restore operations
"""

import subprocess
import os
from pathlib import Path
from typing import List
from utils.logger import Logger
from utils.path_utils import PathUtils


class RegistryManager:
    """Manages Windows registry backup and restore operations"""
    
    def __init__(self):
        """Initialize Registry Manager"""
        self.logger = Logger()
    
    def export_registry_keys(self, registry_keys: List[str], output_dir: str) -> List[str]:
        """
        Export registry keys to .reg files and generate automated restore scripts
        
        Args:
            registry_keys: List of registry key paths
            output_dir: Directory to store exported .reg files
            
        Returns:
            List of successfully exported .reg file paths
        """
        PathUtils.ensure_directory(output_dir)
        exported_files = []
        
        for i, key in enumerate(registry_keys):
            if not key.strip():
                continue
            
            try:
                # Generate descriptive or indexed filename
                sanitized_name = key.replace('\\', '_').replace(':', '').replace(' ', '_')
                filename = f"registry_{i+1}.reg"
                output_file = os.path.join(output_dir, filename)
                
                # Export registry key
                success = self._export_single_key(key, output_file)
                
                if success:
                    exported_files.append(output_file)
                    self.logger.info(f"Exported registry key: {key} -> {filename}")
                else:
                    self.logger.warning(f"Failed to export registry key: {key}")
                    
            except Exception as e:
                self.logger.error(f"Error exporting registry key {key}: {e}")
        
        if exported_files:
            self._create_restore_scripts(output_dir, exported_files)
        
        return exported_files

    def _create_restore_scripts(self, output_dir: str, reg_files: List[str]) -> None:
        """Generate standalone Windows Batch and PowerShell registry restore scripts."""
        try:
            bat_path = os.path.join(output_dir, "restore_registry.bat")
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write("@echo off\n")
                f.write("REM SmartBackup Automated Windows Registry Restoration Script\n")
                f.write("echo Restoring Windows Registry Keys...\n")
                for rf in reg_files:
                    fname = os.path.basename(rf)
                    f.write(f'reg import "%~dp0{fname}"\n')
                f.write("echo Registry restoration complete!\n")

            ps1_path = os.path.join(output_dir, "restore_registry.ps1")
            with open(ps1_path, 'w', encoding='utf-8') as f:
                f.write("# SmartBackup Automated Windows Registry Restoration Script\n")
                f.write("Write-Host 'Restoring Windows Registry Keys...' -ForegroundColor Green\n")
                for rf in reg_files:
                    fname = os.path.basename(rf)
                    f.write(f'reg import "$PSScriptRoot\\{fname}"\n')
                f.write("Write-Host 'Registry restoration complete!' -ForegroundColor Green\n")
            
            self.logger.info("Generated registry restore scripts (restore_registry.bat & restore_registry.ps1)")
        except Exception as e:
            self.logger.error(f"Failed to create registry restore scripts: {e}")

    
    def _export_single_key(self, registry_key: str, output_file: str) -> bool:
        """
        Export a single registry key using Windows reg export
        
        Args:
            registry_key: Registry key path
            output_file: Output .reg file path
            
        Returns:
            True if successful
        """
        try:
            # Build reg export command
            cmd = ['reg', 'export', registry_key, output_file, '/y']
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Check if successful
            if result.returncode == 0:
                return True
            else:
                self.logger.warning(f"Registry export failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during registry export: {e}")
            return False
    
    def import_registry_files(self, reg_files: List[str]) -> int:
        """
        Import .reg files into Windows registry
        
        Args:
            reg_files: List of .reg file paths to import
            
        Returns:
            Number of successfully imported files
        """
        imported_count = 0
        
        for reg_file in reg_files:
            if not os.path.exists(reg_file):
                self.logger.warning(f"Registry file not found: {reg_file}")
                continue
            
            try:
                success = self._import_single_file(reg_file)
                
                if success:
                    imported_count += 1
                    self.logger.info(f"Imported registry file: {reg_file}")
                else:
                    self.logger.warning(f"Failed to import registry file: {reg_file}")
                    
            except Exception as e:
                self.logger.error(f"Error importing registry file {reg_file}: {e}")
        
        return imported_count
    
    def _import_single_file(self, reg_file: str) -> bool:
        """
        Import a single .reg file
        
        Args:
            reg_file: Path to .reg file
            
        Returns:
            True if successful
        """
        try:
            # Build reg import command
            cmd = ['reg', 'import', reg_file]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Check if successful
            if result.returncode == 0:
                return True
            else:
                self.logger.warning(f"Registry import failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during registry import: {e}")
            return False
