"""
Quick Test Script - Verify Functionality
Run this to check if the backup system is working
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    try:
        from engine.app_detector import ApplicationDetector
        print("✓ ApplicationDetector imported")
        
        from engine.backup_engine import BackupEngine
        print("✓ BackupEngine imported")
        
        from engine.registry_manager import RegistryManager
        print("✓ RegistryManager imported")
        
        from utils.logger import Logger
        print("✓ Logger imported")
        
        from utils.path_utils import PathUtils
        print("✓ PathUtils imported")
        
        from utils.system_profiler import SystemProfiler
        print("✓ SystemProfiler imported")
        
        print("\n✅ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_system_profiler():
    """Test system profiler metadata extraction"""
    print("Testing SystemProfiler...")
    try:
        from utils.system_profiler import SystemProfiler
        profiler = SystemProfiler()
        metadata = profiler.get_full_system_metadata()
        
        print(f"  User: {metadata['user_info']['username']} ({metadata['user_info']['domain']})")
        print(f"  Computer Name: {metadata['computer_info']['computer_name']}")
        print(f"  Machine GUID: {metadata['computer_info']['machine_guid']}")
        print(f"  Hardware UUID: {metadata['computer_info']['hardware_uuid']}")
        print(f"  CPU: {metadata['hardware_info']['cpu']}")
        print(f"  RAM: {metadata['hardware_info']['ram']}")
        print(f"  Motherboard: {metadata['hardware_info']['motherboard']}")
        print(f"  OS Product: {metadata['os_info'].get('product_name')} (Build {metadata['os_info'].get('os_build')})")
        
        print("\n✅ SystemProfiler works!\n")
        return True
    except Exception as e:
        print(f"❌ SystemProfiler failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_app_detection():
    """Test application detection"""
    print("Testing application detection...")
    try:
        from engine.app_detector import ApplicationDetector
        
        detector = ApplicationDetector()
        print("Scanning for applications...")
        apps = detector.scan_installed_applications()
        
        if apps:
            print(f"✓ Found {len(apps)} applications")
            print(f"\nFirst 5 apps:")
            for i, app in enumerate(apps[:5], 1):
                print(f"  {i}. {app.display_name}")
            print("\n✅ Application detection works!\n")
            return True
        else:
            print("⚠️  No applications found. Try running as Administrator.\n")
            return False
            
    except Exception as e:
        print(f"❌ Detection failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_path_detection():
    """Test path detection for first app"""
    print("Testing path detection...")
    try:
        from engine.app_detector import ApplicationDetector
        
        detector = ApplicationDetector()
        apps = detector.scan_installed_applications()
        
        if not apps:
            print("⚠️  No apps to test with\n")
            return False
        
        app = apps[0]
        print(f"Testing with: {app.display_name}")
        
        paths = detector.get_application_data_paths(app)
        
        print(f"  User Data Paths: {len(paths['user_data'])}")
        for path in paths['user_data']:
            exists = "✓" if os.path.exists(os.path.expandvars(path)) else "✗"
            print(f"    {exists} {path}")
        
        print(f"  Program Data Paths: {len(paths['program_data'])}")
        for path in paths['program_data']:
            exists = "✓" if os.path.exists(os.path.expandvars(path)) else "✗"
            print(f"    {exists} {path}")
        
        print(f"  Registry Keys: {len(paths['registry_keys'])}")
        for key in paths['registry_keys']:
            print(f"    • {key}")
        
        print("\n✅ Path detection works!\n")
        return True
        
    except Exception as e:
        print(f"❌ Path detection failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SMART APP BACKUP - FUNCTIONALITY TEST")
    print("="*60 + "\n")
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: System Profiler
    results.append(("System Profiler", test_system_profiler()))
    
    # Test 3: App Detection
    results.append(("App Detection", test_app_detection()))
    
    # Test 4: Path Detection
    results.append(("Path Detection", test_path_detection()))

    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    print("="*60 + "\n")
    
    if all(r[1] for r in results):
        print("✅ ALL TESTS PASSED - Ready to use!")
    else:
        print("⚠️  SOME TESTS FAILED - Check errors above")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()