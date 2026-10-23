"""
Admin Utilities Module
Handles administrator privilege detection
"""

import ctypes
import os
import sys


class AdminUtils:
    """Utility functions for administrator privilege checks"""
    
    @staticmethod
    def is_admin() -> bool:
        """
        Check if the application is running with administrator privileges
        
        Returns:
            True if running as administrator
        """
        if os.name == 'nt':  # Windows
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            # For non-Windows systems (should not happen, but fallback)
            return os.geteuid() == 0
    
    @staticmethod
    def request_admin_privileges() -> None:
        """
        Request administrator privileges by relaunching the application
        Note: This will restart the application
        """
        if os.name == 'nt':
            try:
                # Re-run the program with admin rights
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    sys.executable,
                    " ".join(sys.argv),
                    None,
                    1
                )
                sys.exit(0)
            except Exception:
                pass
