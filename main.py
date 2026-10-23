"""
Windows Smart Application Backup Tool
Main entry point for the application
"""

import sys
import os
from pathlib import Path
from gui.main_window import MainWindow

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def main() -> None:
    """Main application entry point"""
    try:
        # Initialize and run the GUI application
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
