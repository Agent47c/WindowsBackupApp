# User Guide: Understanding Application Backups

## How the Backup System Works

### What Gets Backed Up

The Smart Application Backup Tool backs up **configuration data only**:

1. **User Settings**
   - Application preferences
   - User profiles
   - Customizations
   - Themes and color schemes
   - Keyboard shortcuts

2. **Application Data**
   - Recent files lists
   - Project configurations
   - Saved workspaces
   - Extension/plugin settings

3. **Registry Settings**
   - Windows registry keys
   - Application preferences stored in registry
   - File associations (when stored in registry)

### What Does NOT Get Backed Up

The tool **does not** backup:

- ❌ Application executable files (.exe)
- ❌ Program installation files
- ❌ Application binaries
- ❌ Windows system files
- ❌ Drivers
- ❌ Licenses or activation keys (usually)

### Why This Approach?

**Benefits:**
- ✅ Smaller backup size
- ✅ Faster backup/restore
- ✅ No licensing conflicts
- ✅ Safe and reliable
- ✅ Works across Windows versions

**Workflow:**
1. Backup configurations on old system
2. Install application normally on new system
3. Restore configurations
4. Application is configured as before

## Understanding Backup Structure

### Directory Layout

When you create a backup, this structure is created:

```
<Your Chosen Location>/
  └── SmartAppBackup/              [Hidden folder]
      └── <Application Name>/
          ├── ProgramData/         [App shared data]
          ├── UserData/            [User-specific data]
          ├── Registry/            [Registry exports]
          │   ├── registry_key_1.reg
          │   ├── registry_key_2.reg
          │   └── ...
          ├── manifest.json        [Backup metadata]
          └── logs.txt             [Operation log]
```

### Manifest File Explained

The `manifest.json` file contains important metadata:

```json
{
  "version": "1.0.0",
  "app_name": "Visual Studio Code",
  "backup_timestamp": "2025-02-06T14:30:00",
  "windows_username": "YourName",
  "source_paths": {
    "program_data": [],
    "user_data": [
      "%APPDATA%\\Code\\User"
    ]
  },
  "registry_files": [
    "registry_key_1.reg"
  ],
  "backup_directory": "D:\\Backups\\SmartAppBackup\\Visual Studio Code"
}
```

**Field Explanations:**
- `version`: Tool version used for backup
- `app_name`: Name of backed-up application
- `backup_timestamp`: When backup was created
- `windows_username`: Who created the backup
- `source_paths`: Original locations of backed-up data
- `registry_files`: List of registry export files
- `backup_directory`: Where backup is stored

## Environment Variables Guide

### What Are Environment Variables?

Environment variables are shortcuts that represent paths on your system. They make profiles portable across different Windows installations.

### Common Variables

#### User-Specific Locations

**%APPDATA%**
- Full path: `C:\Users\<YourName>\AppData\Roaming`
- Usage: Application settings that roam with your profile
- Examples:
  - `%APPDATA%\Code` (VS Code)
  - `%APPDATA%\Notepad++`

**%LOCALAPPDATA%**
- Full path: `C:\Users\<YourName>\AppData\Local`
- Usage: Local cache and temporary data
- Examples:
  - `%LOCALAPPDATA%\Google\Chrome`
  - `%LOCALAPPDATA%\Microsoft\VSCode`

**%USERPROFILE%**
- Full path: `C:\Users\<YourName>`
- Usage: User home directory
- Examples:
  - `%USERPROFILE%\.ssh`
  - `%USERPROFILE%\.gitconfig`

#### System-Wide Locations

**%PROGRAMFILES%**
- Full path: `C:\Program Files`
- Usage: 64-bit application installations
- Examples:
  - `%PROGRAMFILES%\Notepad++`

**%PROGRAMFILES(X86)%**
- Full path: `C:\Program Files (x86)`
- Usage: 32-bit application installations

**%PROGRAMDATA%**
- Full path: `C:\ProgramData`
- Usage: Shared application data (all users)

### How to View Environment Variables

**Method 1: Command Prompt**
```cmd
echo %APPDATA%
echo %LOCALAPPDATA%
```

**Method 2: Windows Explorer**
1. Open File Explorer
2. Type `%APPDATA%` in the address bar
3. Press Enter

**Method 3: Run Dialog**
1. Press `Win + R`
2. Type `%APPDATA%`
3. Press Enter

## Registry Backup Explained

### What is the Windows Registry?

The Windows Registry is a database that stores system and application settings.

### Registry Key Paths

Format: `HKEY_ROOT\Path\To\Key`

**Common Root Keys:**
- `HKEY_CURRENT_USER` (HKCU): Current user settings
- `HKEY_LOCAL_MACHINE` (HKLM): System-wide settings
- `HKEY_CLASSES_ROOT` (HKCR): File associations

### Example Registry Paths

```
HKEY_CURRENT_USER\Software\Notepad++
HKEY_CURRENT_USER\Software\Microsoft\VSCode
HKEY_CURRENT_USER\Software\Google\Chrome
```

### How Registry Backup Works

1. **Export**: Creates `.reg` file with registry data
2. **Storage**: Saved in `Registry/` folder
3. **Import**: Merges `.reg` file back into registry

### Viewing Registry Files

`.reg` files are text files. You can open them with Notepad:

```reg
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Notepad++]
"Setting1"="Value1"
"Setting2"=dword:00000001
```

## Best Practices

### Before Backup

1. **Close the application** you're backing up
2. **Verify installation paths** are correct
3. **Ensure sufficient disk space** at destination
4. **Run as administrator**

### During Backup

1. **Don't interrupt** the process
2. **Monitor the log window** for errors
3. **Wait for completion message**

### After Backup

1. **Verify backup folder** was created
2. **Check manifest.json** exists
3. **Review logs** for any warnings
4. **Test restore** on the same system first (optional)

### Before Restore

1. **Install the application normally** first
2. **Close the application** before restoring
3. **Decide on overwrite settings**
4. **Backup current settings** (optional)

### During Restore

1. **Don't interrupt** the process
2. **Watch for registry import prompts**
3. **Wait for completion message**

### After Restore

1. **Launch the application**
2. **Verify settings** are restored
3. **Check for any issues**
4. **Review logs** if something seems wrong

## Security Considerations

### What's Safe

- ✅ Backing up application settings
- ✅ Restoring to your own system
- ✅ Using external drives for backups
- ✅ Keeping backups private

### What to Avoid

- ❌ Sharing backups with others (may contain personal data)
- ❌ Restoring from untrusted sources
- ❌ Modifying `.reg` files manually (unless you know what you're doing)
- ❌ Backing up to cloud without encryption

### Privacy Notes

Backups may contain:
- File paths (may reveal your username)
- Recent files lists
- Personal settings
- Application credentials (rarely, but possible)

**Recommendation:** Treat backups as personal data.

## Migration Scenarios

### Scenario 1: Windows Reinstall (Same PC)

1. Before reinstall:
   - Backup all applications
   - Save to external drive
   - Note installation order

2. After reinstall:
   - Install applications
   - Install backup tool
   - Restore each application

### Scenario 2: New Computer

1. Old computer:
   - Create backups
   - Copy to external drive
   - Include profiles folder

2. New computer:
   - Install Windows
   - Install applications
   - Install backup tool
   - Copy profiles folder
   - Restore applications

### Scenario 3: Multiple Computers

1. Use same profiles on all computers
2. Create separate backup locations
3. Restore to appropriate system

## Understanding Logs

### Log File Location

Logs are saved in `logs/` folder:
```
logs/backup_tool_20250206_143000.log
```

### Log Entry Format

```
2025-02-06 14:30:00 - INFO - Starting backup for: VS Code
2025-02-06 14:30:01 - INFO - Created backup structure
2025-02-06 14:30:02 - WARNING - Path does not exist: %PROGRAMFILES%\VSCode
2025-02-06 14:30:03 - INFO - Backed up: C:\Users\Name\AppData\Roaming\Code
2025-02-06 14:30:04 - INFO - Exported registry key: HKCU\Software\Microsoft\VSCode
2025-02-06 14:30:05 - INFO - Backup completed successfully
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Something unexpected but not critical
- **ERROR**: Something failed
- **CRITICAL**: Severe error

### Reading Logs for Troubleshooting

1. Open latest log file in `logs/` folder
2. Search for "ERROR" or "WARNING"
3. Read surrounding context
4. Check what path or operation failed
5. Verify that path exists on your system

## Advanced Topics

### Creating Complex Profiles

For applications with many locations:

```json
{
  "app_name": "Complex Application",
  "program_data_paths": [
    "%PROGRAMFILES%\\App\\config",
    "%PROGRAMFILES%\\App\\plugins",
    "%PROGRAMDATA%\\App\\shared"
  ],
  "user_data_paths": [
    "%APPDATA%\\App\\settings",
    "%APPDATA%\\App\\profiles",
    "%LOCALAPPDATA%\\App\\cache",
    "%USERPROFILE%\\.app"
  ],
  "registry_keys": [
    "HKEY_CURRENT_USER\\Software\\App",
    "HKEY_CURRENT_USER\\Software\\App\\Settings",
    "HKEY_CURRENT_USER\\Software\\App\\Plugins"
  ]
}
```

### Handling Multiple Versions

For applications with version-specific paths:

```json
{
  "app_name": "App (All Versions)",
  "user_data_paths": [
    "%APPDATA%\\App",
    "%APPDATA%\\App 2",
    "%APPDATA%\\App 3",
    "%APPDATA%\\App 4"
  ]
}
```

The tool will only backup paths that exist.

### Excluding Unnecessary Files

Currently, the tool backs up entire directories. Future versions may support exclusion patterns.

**Workaround:** Create separate profiles for different data types.

## Frequently Asked Questions

**Q: Will this backup my application license?**
A: Usually no. Most applications store licenses in protected locations or online. You'll need to reactivate after reinstall.

**Q: Can I backup portable applications?**
A: Yes, but create a profile pointing to the portable app's folder.

**Q: Why are some paths missing in the backup?**
A: Paths that don't exist are skipped. Check logs to see which paths were not found.

**Q: Can I edit the backup manually?**
A: Yes, but it's not recommended. The manifest should match the actual files.

**Q: How much space do backups use?**
A: Varies by application. Usually 10MB - 500MB. Check your original folders' size.

**Q: Can I compress backups?**
A: Not automatically. You can manually zip the backup folder.

**Q: Does this work with all applications?**
A: Works with applications that store data in standard Windows locations. Some applications may use custom locations.

---

## Getting Help

If you encounter issues:

1. Check the logs folder
2. Verify paths in your profile
3. Ensure administrator privileges
4. Check that the application is installed
5. Review this user guide

For profile creation help:
- Use the included _TEMPLATE.json
- Check existing profiles for examples
- Test with one path first
- Expand gradually
