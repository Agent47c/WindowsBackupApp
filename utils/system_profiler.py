"""
System Profiler Module
Collects hardware, OS, computer identification, and user metadata for backup manifests.
"""

import os
import sys
import platform
import subprocess
import winreg
from typing import Dict, Any
from utils.logger import Logger


class SystemProfiler:
    """Collects comprehensive hardware, OS, computer ID, and user metadata."""

    def __init__(self):
        self.logger = Logger()

    @staticmethod
    def get_machine_guid() -> str:
        """Get Windows Machine GUID from registry."""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return str(guid)
        except Exception:
            return "Unknown-Machine-GUID"

    @staticmethod
    def get_hardware_uuid() -> str:
        """Get Hardware UUID via PowerShell/WMI."""
        try:
            cmd = ['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_ComputerSystemProduct).UUID']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return "Unknown-Hardware-UUID"

    @staticmethod
    def get_cpu_info() -> str:
        """Get CPU Processor Name."""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                processor, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                return str(processor).strip()
        except Exception:
            return platform.processor() or "Unknown CPU"

    @staticmethod
    def get_total_ram_gb() -> str:
        """Get Total Physical Installed Memory in GB."""
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                gb = stat.ullTotalPhys / (1024 ** 3)
                return f"{gb:.2f} GB"
        except Exception:
            pass
        return "Unknown RAM"

    @staticmethod
    def get_motherboard_info() -> str:
        """Get Motherboard Manufacturer and Product model."""
        try:
            cmd = ['powershell', '-NoProfile', '-Command', 
                   '$b = Get-CimInstance Win32_BaseBoard; "$($b.Manufacturer) $($b.Product)"']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return "Unknown Motherboard"

    @staticmethod
    def get_os_info() -> Dict[str, str]:
        """Get OS Name, Build, Version, Architecture."""
        os_info = {
            'os_name': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'os_architecture': platform.architecture()[0],
            'os_build': 'Unknown',
            'product_name': 'Windows'
        }
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                try:
                    product_name, _ = winreg.QueryValueEx(key, "ProductName")
                    os_info['product_name'] = str(product_name)
                except Exception:
                    pass
                try:
                    build, _ = winreg.QueryValueEx(key, "CurrentBuildNumber")
                    os_info['os_build'] = str(build)
                except Exception:
                    pass
                try:
                    display_ver, _ = winreg.QueryValueEx(key, "DisplayVersion")
                    os_info['display_version'] = str(display_ver)
                except Exception:
                    pass
        except Exception:
            pass
        return os_info

    def get_full_system_metadata(self) -> Dict[str, Any]:
        """
        Get complete system, hardware, computer ID, user, and OS metadata.
        """
        os_data = self.get_os_info()
        user_name = os.environ.get('USERNAME') or os.getlogin() or 'UnknownUser'
        user_domain = os.environ.get('USERDOMAIN') or os.environ.get('COMPUTERNAME') or 'Local'

        metadata = {
            'user_info': {
                'username': user_name,
                'domain': user_domain,
                'user_profile': os.environ.get('USERPROFILE', '')
            },
            'computer_info': {
                'computer_name': os.environ.get('COMPUTERNAME') or platform.node(),
                'machine_guid': self.get_machine_guid(),
                'hardware_uuid': self.get_hardware_uuid(),
            },
            'hardware_info': {
                'cpu': self.get_cpu_info(),
                'ram': self.get_total_ram_gb(),
                'motherboard': self.get_motherboard_info(),
                'architecture': platform.machine()
            },
            'os_info': os_data
        }
        return metadata
