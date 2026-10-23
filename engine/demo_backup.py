"""
Demo Script - Testing Backup Functionality
This script demonstrates how the backup system works
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.backup_engine import BackupEngine
from engine.app_detector import ApplicationDetector
from utils.logger import Logger

def demo_backup():
    """Demonstrate backup functionality"""
    
    logger = Logger()
    print("\n" + "="*60)
    print("SMART APPLICATION BACKUP - DEMO")
    print("="*60 + "\n")
    
    # Initialize components
    print("1. Initializing backup engine...")
    backup_engine = BackupEngine()
    app_detector = ApplicationDetector()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  → {message}")
    
    backup_engine.set_progress_callback(progress_callback)
    
    # Scan for applications
    print("\n2. Scanning for installed applications...")
    apps = app_detector.scan_installed_applications()
    
    if not apps:
        print("  ❌ No applications found. Try running as Administrator.")
        return
    
    print(f"  ✅ Found {len(apps)} applications")
    print(f"\nSample applications detected:")
    for i, app in enumerate(apps[:10], 1):
        print(f"  {i}. {app.display_name}")
        if app.version:
            print(f"     Version: {app.version}")
        if app.publisher:
            print(f"     Publisher: {app.publisher}")
        print()
    
    # Select first app for demo
    if len(apps) > 0:
        selected_app = apps[0]
        print(f"\n3. Selected for demo: {selected_app.display_name}")
        
        # Detect data paths
        print("\n4. Detecting data paths...")
        data_paths = app_detector.get_application_data_paths(selected_app)
        
        print(f"  Program Data Paths: {len(data_paths['program_data'])} found")
        for path in data_paths['program_data']:
            print(f"    • {path}")
        
        print(f"  User Data Paths: {len(data_paths['user_data'])} found")
        for path in data_paths['user_data']:
            print(f"    • {path}")
        
        print(f"  Registry Keys: {len(data_paths['registry_keys'])} found")
        for key in data_paths['registry_keys']:
            print(f"    • {key}")
        
        # Show what would be backed up
        print("\n5. Backup Preview:")
        print("  The backup would:")
        print("  a. Create folder structure:")
        print("     SmartAppBackup/")
        print(f"     └── {selected_app.display_name}/")
        print("         ├── manifest.json")
        print("         ├── ProgramData/")
        print("         ├── UserData/")
        print("         └── Registry/")
        
        print("\n  b. Copy files from detected paths")
        print("  c. Export registry keys to .reg files")
        print("  d. Create manifest with metadata")
        print("  e. Update backup history")
        
        # Ask if user wants to perform actual backup
        print("\n" + "="*60)
        choice = input("\nWould you like to perform actual backup? (y/n): ")
        
        if choice.lower() == 'y':
            backup_dir = input("Enter backup destination (e.g., D:\\Backups): ").strip()
            
            if backup_dir and os.path.exists(backup_dir):
                print(f"\n6. Starting backup to: {backup_dir}")
                print("-"*60)
                
                success = backup_engine.backup_application(
                    selected_app.display_name,
                    data_paths,
                    backup_dir
                )
                
                print("-"*60)
                if success:
                    print("\n✅ BACKUP COMPLETED SUCCESSFULLY!")
                    print(f"\nBackup location:")
                    print(f"  {backup_dir}\\SmartAppBackup\\{selected_app.display_name}")
                else:
                    print("\n❌ BACKUP FAILED - Check logs for details")
            else:
                print("  ❌ Invalid backup destination")
        else:
            print("\n  Demo completed without performing backup")
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        demo_backup()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
