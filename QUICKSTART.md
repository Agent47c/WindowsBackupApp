# Quick Start Guide

## Windows Smart Application Backup Tool

### Still Under Development
### Installation Steps

1. **Verify Python Installation**
   ```bash
   python --version
   ```
   Should show Python 3.10 or higher

2. **Navigate to Application Directory**
   ```bash
   cd SmartAppBackup
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```
   
   Or right-click `main.py` → "Run as administrator"

### First Time Setup

1. **Application will request administrator privileges**
   - Click "Yes" to grant access
   - Required for registry backup/restore operations

2. **Check the profiles directory**
   - Sample profiles are included:
     - Notepad++
     - Visual Studio Code
     - Google Chrome

3. **Review the logs folder**
   - A new log file is created each session
   - Check here for detailed operation information

### Testing the Application

#### Test 1: Backup an Application

1. Select "Notepad++" from dropdown (or any installed app)
2. Click "Backup Application"
3. Choose a test destination folder (e.g., Desktop)
4. Wait for completion
5. Verify backup folder structure:
   ```
   <Destination>/SmartAppBackup/Notepad++/
       ├── ProgramData/
       ├── UserData/
       ├── Registry/
       └── manifest.json
   ```

#### Test 2: Restore an Application

1. Click "Restore Application"
2. Select the backup folder created in Test 1
3. Choose "Yes" to overwrite or "No" to skip existing files
4. Wait for completion
5. Check logs for confirmation

### Creating Your First Custom Profile

1. Create a new file: `profiles/myapp.json`

2. Use this template:
   ```json
   {
     "app_name": "My Application",
     "program_data_paths": [
       "%PROGRAMFILES%\\MyApp\\config"
     ],
     "user_data_paths": [
       "%APPDATA%\\MyApp"
     ],
     "registry_keys": [
       "HKEY_CURRENT_USER\\Software\\MyApp"
     ]
   }
   ```

3. Replace paths with your application's actual paths

4. Restart the application to load the new profile

### Finding Application Data Locations

#### Method 1: Windows Environment Variables
Open Command Prompt and type:
```cmd
echo %APPDATA%
echo %LOCALAPPDATA%
echo %PROGRAMFILES%
```

#### Method 2: Manual Search
Common locations:
- User Settings: `C:\Users\<YourName>\AppData\Roaming\<AppName>`
- Local Cache: `C:\Users\<YourName>\AppData\Local\<AppName>`
- Program Config: `C:\Program Files\<AppName>\config`

#### Method 3: Registry Editor
1. Press `Win + R`
2. Type `regedit` and press Enter
3. Navigate to: `HKEY_CURRENT_USER\Software`
4. Look for your application name

### Common Environment Variables Reference

| Variable | Typical Path | Use Case |
|----------|--------------|----------|
| %APPDATA% | C:\Users\User\AppData\Roaming | User settings, profiles |
| %LOCALAPPDATA% | C:\Users\User\AppData\Local | Cache, temporary data |
| %USERPROFILE% | C:\Users\User | User home directory |
| %PROGRAMFILES% | C:\Program Files | 64-bit programs |
| %PROGRAMFILES(X86)% | C:\Program Files (x86) | 32-bit programs |
| %PROGRAMDATA% | C:\ProgramData | Shared program data |

### Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| No profiles shown | Add .json files to profiles/ folder |
| Admin error | Run as administrator |
| Registry export fails | Check key paths, run as admin |
| Backup folder empty | Check source paths exist, view logs |
| Restore not working | Ensure app is reinstalled first |

### Best Practices

1. **Always reinstall the application before restoring**
   - The tool restores configuration, not the program itself

2. **Test profiles on a single app first**
   - Verify paths are correct before creating many profiles

3. **Keep backups organized**
   - Use descriptive destination folder names
   - Include dates in backup locations

4. **Review logs after operations**
   - Logs show exactly what was backed up/restored
   - Check for warnings about missing paths

5. **Backup to external drives**
   - More reliable for system migrations
   - Protects against drive failures

### Example Workflow: New PC Setup

1. **Old PC:**
   - Run Smart Application Backup Tool
   - Backup all configured applications
   - Save to external drive

2. **New PC:**
   - Install Windows
   - Reinstall all applications normally
   - Install Smart Application Backup Tool
   - Copy profiles/ folder from old PC
   - Restore each application

3. **Result:**
   - All settings, preferences, and configurations restored
   - No need to reconfigure each application manually

### Advanced: Batch Profile Creation

Create multiple profiles quickly:

1. Find application data paths on your system
2. Copy the template JSON
3. Modify only the app_name and paths
4. Save with descriptive filename
5. Restart application to load

### Support Resources

- **Logs**: `logs/` folder for detailed operation records
- **Profiles**: `profiles/` folder for configuration templates
- **README.md**: Complete documentation
- **manifest.json**: In each backup, shows what was saved

---

**Ready to Start?**

Run: `python main.py`

**Questions?**

Check the logs folder for detailed information about any errors or warnings.
