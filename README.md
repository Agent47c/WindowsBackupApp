# Windows Smart Application Backup Tool

A Python-based desktop application for backing up and restoring Windows application configurations, user data, and registry settings.

## Overview

This tool allows you to safely backup and restore application-specific configuration data without attempting to backup the entire application installation. It's perfect for:

- Migrating to a new Windows system
- Recovering after a Windows reinstallation
- Creating portable configuration backups
- Quickly restoring your personalized application settings

## Features

- **Profile-Based Backups**: Define custom backup profiles for any application
- **Registry Backup**: Safely export and import application registry settings
- **User-Friendly GUI**: Simple Tkinter-based interface
- **Comprehensive Logging**: Detailed operation logs for troubleshooting
- **Manifest System**: Track what was backed up for reliable restoration
- **Safe Path Validation**: Prevents backing up system-critical directories

## Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: Version 3.10 or higher
- **Permissions**: Administrator privileges (for registry operations)

## Installation

1. **Install Python 3.10+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure "Add Python to PATH" is checked during installation

2. **Clone or Download this Repository**
   ```bash
   git clone <repository-url>
   cd SmartAppBackup
   ```

3. **No Additional Dependencies Required**
   - Uses only Python standard library (Tkinter)

## Usage

### Running the Application

1. **Run as Administrator** (required for registry operations):
   ```bash
   python main.py
   ```

2. The application will automatically prompt for administrator privileges if needed

### Backing Up an Application

1. Select an application from the dropdown menu
2. Click "Backup Application"
3. Choose a destination folder
4. Wait for the backup to complete

The backup will be saved in:
```
<Destination>/SmartAppBackup/<ApplicationName>/
    ├── ProgramData/
    ├── UserData/
    ├── Registry/
    ├── manifest.json
    └── logs.txt
```

### Restoring an Application

1. **Reinstall the application normally first**
2. Click "Restore Application"
3. Select the backup folder
4. Choose whether to overwrite existing files
5. Wait for the restore to complete

## Creating Custom Profiles

Profiles are JSON files stored in the `profiles/` directory. Each profile defines what to backup for a specific application.

### Profile Format

Create a file named `<app_name>.json` in the `profiles/` folder:

```json
{
  "app_name": "Application Name",
  "program_data_paths": [
    "%PROGRAMFILES%\\AppName\\config",
    "%PROGRAMDATA%\\AppName"
  ],
  "user_data_paths": [
    "%APPDATA%\\AppName",
    "%LOCALAPPDATA%\\AppName"
  ],
  "registry_keys": [
    "HKEY_CURRENT_USER\\Software\\AppName"
  ]
}
```

### Supported Environment Variables

- `%APPDATA%` - User's application data folder
- `%LOCALAPPDATA%` - User's local application data folder
- `%USERPROFILE%` - User's profile folder
- `%PROGRAMFILES%` - Program Files folder
- `%PROGRAMFILES(X86)%` - Program Files (x86) folder
- `%PROGRAMDATA%` - ProgramData folder

### Example Profiles Included

1. **Notepad++** (`notepad_plusplus.json`)
2. **Visual Studio Code** (`vscode.json`)
3. **Google Chrome** (`chrome.json`)

## Project Structure

```
SmartAppBackup/
├── main.py                     # Application entry point
├── gui/
│   ├── __init__.py
│   └── main_window.py         # Main GUI window
├── engine/
│   ├── __init__.py
│   ├── profile_manager.py     # Profile loading and validation
│   ├── backup_engine.py       # Backup operations
│   ├── restore_engine.py      # Restore operations
│   ├── registry_manager.py    # Registry backup/restore
│   └── manifest_manager.py    # Metadata management
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging system
│   ├── path_utils.py          # Path handling utilities
│   └── admin_utils.py         # Admin privilege checks
├── profiles/                   # Application profile definitions
│   ├── notepad_plusplus.json
│   ├── vscode.json
│   └── chrome.json
└── logs/                       # Operation logs (auto-created)
```

## Safety Features

1. **Path Validation**: Blocks backup of system-critical directories
2. **Manifest Tracking**: Records exactly what was backed up
3. **Overwrite Protection**: Option to skip existing files during restore
4. **Comprehensive Logging**: All operations are logged with timestamps
5. **Error Handling**: Graceful failure with informative messages

## Limitations (MVP)

This MVP does not include:

- Application executable backup
- Incremental/differential backups
- Compression
- Cloud synchronization
- Scheduled backups
- Multi-application batch operations

## Troubleshooting

### "Administrator Privileges Required"
- Right-click `main.py` and select "Run as administrator"
- Or run Command Prompt as administrator, then execute `python main.py`

### "No profiles found"
- Ensure JSON files exist in the `profiles/` folder
- Check JSON syntax is valid
- Verify file extension is `.json`

### Registry export/import fails
- Ensure running as administrator
- Check registry key paths are correct
- Verify keys exist on your system

### Backup directory empty
- Check if source paths exist (view logs)
- Verify environment variables expand correctly
- Ensure you have read permissions for source directories

## Logs

Operation logs are automatically saved in the `logs/` directory with timestamps:
```
logs/backup_tool_YYYYMMDD_HHMMSS.log
```

## License

This project is provided as-is for educational and personal use.

## Contributing

To add support for a new application:

1. Create a new JSON profile in the `profiles/` folder
2. Test the backup and restore process
3. Document any special considerations

## Support

For issues or questions:
- Check the logs folder for detailed error information
- Verify administrator privileges
- Ensure profile JSON syntax is correct
- Review the application's actual data locations

## Version

**Current Version**: 1.0.0 (MVP)
**Last Updated**: 2025

## Acknowledgments

Built following clean architecture principles with modular, maintainable code structure.
