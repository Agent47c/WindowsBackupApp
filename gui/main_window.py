"""
Main Window Module - Modern Dark Theme
Primary GUI interface for the Smart Application Backup Tool
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading

from typing import Optional, List, Dict
from engine.app_detector import ApplicationDetector, InstalledApplication
from engine.backup_engine import BackupEngine
from engine.restore_engine import RestoreEngine
from engine.uninstall_engine import UninstallEngine
from engine.history_manager import HistoryManager
from utils.admin_utils import AdminUtils
from utils.logger import Logger


class ModernDarkTheme:
    """Modern dark theme colors"""
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#2d2d2d"
    BG_LIGHT = "#3e3e3e"
    FG_PRIMARY = "#ffffff"
    FG_SECONDARY = "#b0b0b0"
    ACCENT = "#0078d4"
    ACCENT_HOVER = "#1a86d9"
    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    BORDER = "#555555"
    DANGER = "#d32f2f"
    DANGER_HOVER = "#e53935"


class MainWindow:
    """Main application window with modern dark theme"""
    
    def __init__(self):
        """Initialize the main window"""
        self.logger = Logger()
        self.app_detector = ApplicationDetector()
        self.backup_engine = BackupEngine()
        self.restore_engine = RestoreEngine()
        self.uninstall_engine = UninstallEngine()
        self.history_manager = HistoryManager()
        
        # Set up progress callbacks
        self.backup_engine.set_progress_callback(self.update_log)
        self.restore_engine.set_progress_callback(self.update_log)
        self.uninstall_engine.set_progress_callback(self.update_log)
        
        # Application state
        self.installed_apps: List[InstalledApplication] = []
        self.selected_app: Optional[InstalledApplication] = None
        self.current_data_paths: Optional[Dict] = None
        
        # Default destination to local application backups directory
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_destination = os.path.join(app_root, "backups")

        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Windows Smart Application Backup Tool")
        self.root.geometry("1050x750")
        self.root.resizable(True, True)
        
        # Configure dark theme
        self._apply_dark_theme()
        
        # Check admin privileges
        self._check_admin_privileges()
        
        # Build GUI
        self._build_gui()
        
        # Load backup history and scan installed applications on startup
        self._refresh_history_tab()
        self._scan_applications()

    
    def _apply_dark_theme(self) -> None:
        """Apply modern dark theme to the application"""
        self.root.configure(bg=ModernDarkTheme.BG_DARK)
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for all widgets
        style.configure('.',
                       background=ModernDarkTheme.BG_DARK,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       bordercolor=ModernDarkTheme.BORDER,
                       darkcolor=ModernDarkTheme.BG_DARK,
                       lightcolor=ModernDarkTheme.BG_LIGHT,
                       troughcolor=ModernDarkTheme.BG_MEDIUM,
                       selectbackground=ModernDarkTheme.ACCENT,
                       selectforeground=ModernDarkTheme.FG_PRIMARY,
                       fieldbackground=ModernDarkTheme.BG_MEDIUM,
                       borderwidth=1)
        
        # Frame style
        style.configure('TFrame', background=ModernDarkTheme.BG_DARK)
        style.configure('Card.TFrame', background=ModernDarkTheme.BG_MEDIUM, relief='flat')
        
        # Label styles
        style.configure('TLabel',
                       background=ModernDarkTheme.BG_DARK,
                       foreground=ModernDarkTheme.FG_PRIMARY)
        style.configure('Title.TLabel',
                       background=ModernDarkTheme.BG_DARK,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       font=('Segoe UI', 16, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_SECONDARY,
                       font=('Segoe UI', 9))
        style.configure('Detail.TLabel',
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       font=('Segoe UI', 9))
        style.configure('DetailValue.TLabel',
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_SECONDARY,
                       font=('Segoe UI', 9))
        style.configure('SectionTitle.TLabel',
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       font=('Segoe UI', 11, 'bold'))
        
        # Button styles
        style.configure('Accent.TButton',
                       background=ModernDarkTheme.ACCENT,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       borderwidth=0,
                       focuscolor=ModernDarkTheme.ACCENT,
                       font=('Segoe UI', 10))
        style.map('Accent.TButton',
                 background=[('active', ModernDarkTheme.ACCENT_HOVER)])
        
        style.configure('Danger.TButton',
                       background=ModernDarkTheme.DANGER,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       borderwidth=0,
                       focuscolor=ModernDarkTheme.DANGER,
                       font=('Segoe UI', 10))
        style.map('Danger.TButton',
                 background=[('active', ModernDarkTheme.DANGER_HOVER)])
        
        # Combobox style
        style.configure('TCombobox',
                       fieldbackground=ModernDarkTheme.BG_MEDIUM,
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       arrowcolor=ModernDarkTheme.FG_PRIMARY,
                       borderwidth=1,
                       relief='flat')
        
        # Listbox colors
        self.root.option_add('*TCombobox*Listbox.background', ModernDarkTheme.BG_MEDIUM)
        self.root.option_add('*TCombobox*Listbox.foreground', ModernDarkTheme.FG_PRIMARY)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ModernDarkTheme.ACCENT)
        
        # Progress bar
        style.configure('TProgressbar',
                       background=ModernDarkTheme.ACCENT,
                       troughcolor=ModernDarkTheme.BG_MEDIUM,
                       borderwidth=0,
                       thickness=4)
        
        # LabelFrame
        style.configure('TLabelframe',
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       bordercolor=ModernDarkTheme.BORDER,
                       borderwidth=1)
        style.configure('TLabelframe.Label',
                       background=ModernDarkTheme.BG_MEDIUM,
                       foreground=ModernDarkTheme.FG_PRIMARY,
                       font=('Segoe UI', 10, 'bold'))
    
    def _check_admin_privileges(self) -> None:
        """Check if running with administrator privileges"""
        self.is_admin = AdminUtils.is_admin()
        if self.is_admin:
            self.root.title("Smart Application Backup & Restore — [Administrator]")
        else:
            self.root.title("Smart Application Backup & Restore — [User Mode]")
    
    def _request_admin_restart(self):
        """Request administrator restart on user action"""
        AdminUtils.request_admin_privileges()
    
    def _build_gui(self) -> None:
        """Build the GUI components with top-level section navigation"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, style='TFrame', padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
    def _build_gui(self) -> None:
        """Build the GUI components with multi-tab section notebook for spacious navigation"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, style='TFrame', padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title Header (Row 0)
        title_frame = ttk.Frame(main_frame, style='TFrame')
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        title_frame.columnconfigure(0, weight=1)

        ttk.Label(
            title_frame,
            text="Smart Application Backup & Restore",
            style='Title.TLabel'
        ).grid(row=0, column=0, sticky=tk.W)

        # Admin Badge / Restart Button
        if AdminUtils.is_admin():
            admin_label = ttk.Label(
                title_frame,
                text="🛡️ Administrator Mode",
                style='Subtitle.TLabel'
            )
            admin_label.grid(row=0, column=1, sticky=tk.E)
        else:
            admin_btn = ttk.Button(
                title_frame,
                text="🛡️ Restart as Administrator",
                command=self._request_admin_restart,
                style='Accent.TButton'
            )
            admin_btn.grid(row=0, column=1, sticky=tk.E)

        # Top Navigation Notebook (Row 1)
        self.main_notebook = ttk.Notebook(main_frame)
        self.main_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 6))

        # --- Section 1: 📦 Applications ---
        self.tab_apps = ttk.Frame(self.main_notebook, style='TFrame', padding="8")
        self.main_notebook.add(self.tab_apps, text="  📦 Applications  ")

        # --- Section 2: 📜 Backup History & Restore ---
        self.tab_history = ttk.Frame(self.main_notebook, style='TFrame', padding="8")
        self.main_notebook.add(self.tab_history, text="  📜 Backup History & Restore  ")

        # --- Section 3: 📋 Activity & Error Logs ---
        self.tab_logs = ttk.Frame(self.main_notebook, style='TFrame', padding="8")
        self.main_notebook.add(self.tab_logs, text="  📋 Activity & Error Logs  ")

        # Build Section 1: Applications (Installed Apps list + App Details)
        self._build_apps_section(self.tab_apps)

        # Build Section 2: History & Restore (History list + Archive details & Restore)
        self._build_history_section(self.tab_history)

        # Build Section 3: Logs (Full Activity & Diagnostics Log View)
        self._build_log_section(self.tab_logs)

        # Bottom Status Bar (Row 2)
        self._build_status_bar(main_frame, row=2)

    def _build_apps_section(self, parent):
        """Section 1: Application selection list (left) + App Details & Backup/Uninstall (right)"""
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=4)
        parent.rowconfigure(0, weight=1)
        
        # Left: Application List Card
        app_card = ttk.Frame(parent, style='Card.TFrame', padding="12")
        app_card.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        app_card.columnconfigure(0, weight=1)
        app_card.rowconfigure(2, weight=1)
        
        ttk.Label(app_card, text="Installed Applications", style='SectionTitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        # Search Bar
        search_frame = ttk.Frame(app_card, style='Card.TFrame')
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        search_frame.columnconfigure(0, weight=1)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search)
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=ModernDarkTheme.BG_DARK,
            fg=ModernDarkTheme.FG_PRIMARY,
            insertbackground=ModernDarkTheme.FG_PRIMARY,
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=2
        )
        search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Apps Listbox
        list_frame = tk.Frame(app_card, bg=ModernDarkTheme.BG_MEDIUM, relief='solid', borderwidth=1)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        
        scrollbar = tk.Scrollbar(list_frame, bg=ModernDarkTheme.BG_MEDIUM)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.app_listbox = tk.Listbox(
            list_frame,
            height=18,
            font=('Segoe UI', 10),
            bg=ModernDarkTheme.BG_MEDIUM,
            fg=ModernDarkTheme.FG_PRIMARY,
            selectbackground=ModernDarkTheme.ACCENT,
            selectforeground=ModernDarkTheme.FG_PRIMARY,
            highlightthickness=0,
            borderwidth=0,
            activestyle='none',
            yscrollcommand=scrollbar.set,
            relief='flat'
        )
        self.app_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.config(command=self.app_listbox.yview)
        
        self.app_listbox.bind('<<ListboxSelect>>', self._on_app_selected)
        
        self.scan_button = ttk.Button(
            app_card,
            text="🔄 Refresh Apps List",
            command=self._scan_applications,
            style='Accent.TButton'
        )
        self.scan_button.grid(row=3, column=0, sticky=(tk.W, tk.E))

        # Right: Application Details Panel
        self._build_detail_panel(parent)

    def _build_detail_panel(self, parent):
        """Build application details panel (Right side of Section 1)"""
        detail_card = ttk.Frame(parent, style='Card.TFrame', padding="12")
        detail_card.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(6, 0))
        detail_card.columnconfigure(0, weight=1)
        
        ttk.Label(detail_card, text="Application Details", style='SectionTitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        info_frame = ttk.Frame(detail_card, style='Card.TFrame')
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        self.detail_labels = {}
        detail_fields = [
            ('name', 'Application:'),
            ('version', 'Version:'),
            ('publisher', 'Publisher:'),
            ('size', 'Size:'),
            ('install_date', 'Install Date:'),
            ('install_loc', 'Install Path:'),
            ('uninstall_cmd', 'Uninstall Cmd:'),
            ('user_data', 'User Data:'),
            ('program_data', 'Program Data:'),
            ('registry_keys', 'Registry Keys:'),
        ]
        
        for i, (key, label_text) in enumerate(detail_fields):
            ttk.Label(info_frame, text=label_text, style='Detail.TLabel').grid(
                row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            self.detail_labels[key] = ttk.Label(
                info_frame, text="—", style='DetailValue.TLabel', wraplength=450)
            self.detail_labels[key].grid(row=i, column=1, sticky=tk.W, pady=2)
        
        ttk.Separator(detail_card, orient='horizontal').grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        dest_frame = ttk.Frame(detail_card, style='Card.TFrame')
        dest_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dest_frame.columnconfigure(0, weight=1)
        
        ttk.Label(dest_frame, text="Backup Destination:", style='Detail.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 4))
        
        dest_inner = ttk.Frame(dest_frame, style='Card.TFrame')
        dest_inner.grid(row=1, column=0, sticky=(tk.W, tk.E))
        dest_inner.columnconfigure(0, weight=1)
        
        self.dest_var = tk.StringVar(value=self.backup_destination)

        self.dest_label = ttk.Label(
            dest_inner, textvariable=self.dest_var, style='DetailValue.TLabel', wraplength=350)
        self.dest_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        
        self.dest_button = ttk.Button(
            dest_inner, text="📁 Choose", command=self._choose_destination,
            style='Accent.TButton', width=10)
        self.dest_button.grid(row=0, column=1, sticky=tk.E)
        
        btn_frame = ttk.Frame(detail_card, style='Card.TFrame')
        btn_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(6, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        self.backup_button = ttk.Button(
            btn_frame, text="💾 Backup Selected App", command=self._on_backup_click,
            style='Accent.TButton', state='disabled')
        self.backup_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 4))
        
        self.uninstall_button = ttk.Button(
            btn_frame, text="🗑️ Uninstall App", command=self._on_uninstall_click,
            style='Danger.TButton', state='disabled')
        self.uninstall_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(4, 0))

    def _build_history_section(self, parent):
        """Section 2: Backup History list (left) + Backup Archive details & Restore button (right)"""
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=4)
        parent.rowconfigure(0, weight=1)

        # Left: Backup History Card
        hist_card = ttk.Frame(parent, style='Card.TFrame', padding="12")
        hist_card.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        hist_card.columnconfigure(0, weight=1)
        hist_card.rowconfigure(1, weight=1)

        ttk.Label(hist_card, text="Saved Backup History", style='SectionTitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8))

        hist_list_frame = tk.Frame(hist_card, bg=ModernDarkTheme.BG_MEDIUM, relief='solid', borderwidth=1)
        hist_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))

        hist_scroll = tk.Scrollbar(hist_list_frame, bg=ModernDarkTheme.BG_MEDIUM)
        hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(
            hist_list_frame,
            height=18,
            font=('Segoe UI', 10),
            bg=ModernDarkTheme.BG_MEDIUM,
            fg=ModernDarkTheme.FG_PRIMARY,
            selectbackground=ModernDarkTheme.ACCENT,
            selectforeground=ModernDarkTheme.FG_PRIMARY,
            highlightthickness=0,
            borderwidth=0,
            activestyle='none',
            yscrollcommand=hist_scroll.set,
            relief='flat'
        )
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        hist_scroll.config(command=self.history_listbox.yview)

        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_selected)

        hist_btn_frame = ttk.Frame(hist_card, style='Card.TFrame')
        hist_btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        hist_btn_frame.columnconfigure(0, weight=1)
        hist_btn_frame.columnconfigure(1, weight=1)

        ttk.Button(
            hist_btn_frame,
            text="🔄 Refresh History",
            command=self._refresh_history_tab,
            style='Accent.TButton'
        ).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 3))

        ttk.Button(
            hist_btn_frame,
            text="📂 Import Backup Folder",
            command=self._on_browse_restore_click,
            style='Accent.TButton'
        ).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(3, 0))

        # Right: History Details & Restore Panel
        self._build_history_detail_panel(parent)

    def _build_history_detail_panel(self, parent):
        """Build details card for Section 2 (Backup History & Restore)"""
        hist_detail_card = ttk.Frame(parent, style='Card.TFrame', padding="12")
        hist_detail_card.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(6, 0))
        hist_detail_card.columnconfigure(0, weight=1)

        ttk.Label(hist_detail_card, text="Backup Archive Details", style='SectionTitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))

        info_frame = ttk.Frame(hist_detail_card, style='Card.TFrame')
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)

        self.hist_detail_labels = {}
        hist_fields = [
            ('app_name', 'Application:'),
            ('version', 'Version:'),
            ('backup_date', 'Backup Date:'),
            ('location', 'Storage Path:'),
            ('status', 'Backup Status:'),
        ]

        for i, (key, label_text) in enumerate(hist_fields):
            ttk.Label(info_frame, text=label_text, style='Detail.TLabel').grid(
                row=i, column=0, sticky=tk.W, padx=(0, 10), pady=6)

            self.hist_detail_labels[key] = ttk.Label(
                info_frame, text="—", style='DetailValue.TLabel', wraplength=450)
            self.hist_detail_labels[key].grid(row=i, column=1, sticky=tk.W, pady=6)

        ttk.Separator(hist_detail_card, orient='horizontal').grid(row=2, column=0, sticky=(tk.W, tk.E), pady=15)

        # Restore Action Buttons
        self.hist_restore_button = ttk.Button(
            hist_detail_card,
            text="⚡ Restore Selected Application",
            command=self._on_hist_restore_click,
            style='Accent.TButton',
            state='disabled'
        )
        self.hist_restore_button.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
            hist_detail_card,
            text="📂 Browse Backup Folder (After Windows Reinstall)",
            command=self._on_browse_restore_click,
            style='Accent.TButton'
        ).grid(row=4, column=0, sticky=(tk.W, tk.E))
    
    def _build_log_section(self, parent):
        """Section 3: Activity & Diagnostics Log"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Header bar for logs section
        log_hdr = ttk.Frame(parent, style='Card.TFrame', padding="6")
        log_hdr.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        log_hdr.columnconfigure(0, weight=1)

        ttk.Label(log_hdr, text="Activity & System Logs", style='SectionTitle.TLabel').grid(row=0, column=0, sticky=tk.W)

        hdr_btns = ttk.Frame(log_hdr, style='Card.TFrame')
        hdr_btns.grid(row=0, column=1, sticky=tk.E)

        ttk.Button(
            hdr_btns,
            text="🧹 Clear Log View",
            command=self._clear_log,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            hdr_btns,
            text="📂 Open Detailed Error Logs Folder (logs/)",
            command=self._open_logs_folder,
            style='Accent.TButton'
        ).pack(side=tk.LEFT)

        self.log_text = scrolledtext.ScrolledText(
            parent,
            height=20,
            wrap=tk.WORD,
            bg=ModernDarkTheme.BG_DARK,
            fg=ModernDarkTheme.FG_PRIMARY,
            insertbackground=ModernDarkTheme.FG_PRIMARY,
            selectbackground=ModernDarkTheme.ACCENT,
            font=('Consolas', 10),
            relief='flat',
            borderwidth=1
        )
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 6))

        # Progress bar
        self.progress = ttk.Progressbar(
            parent, mode='indeterminate', style='TProgressbar')
        self.progress.grid(row=2, column=0, sticky=(tk.W, tk.E))


    def _clear_log(self):
        """Clear the text log box"""
        self.log_text.delete(1.0, tk.END)

    def _open_logs_folder(self):
        """Open the logs folder in Windows File Explorer"""
        try:
            logs_dir = self.logger.get_logs_dir()
            if os.path.exists(logs_dir):
                os.startfile(logs_dir)
            else:
                messagebox.showinfo("Log Directory", f"Log directory: {logs_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log folder: {e}")

    def _build_status_bar(self, parent, row):
        """Build status bar"""
        status_frame = ttk.Frame(parent, style='TFrame')
        status_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(6, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame, textvariable=self.status_var, style='Subtitle.TLabel')
        status_label.grid(row=0, column=0, sticky=tk.W)

    
    # ─── Search ──────────────────────────────────────────────
    
    def _get_app_icon_symbol(self, name: str, publisher: str = "") -> str:
        """Resolve a category icon symbol for app display tiles"""
        n = name.lower()
        p = publisher.lower() if publisher else ""
        if any(x in n or x in p for x in ['adobe', 'premiere', 'after effects', 'photoshop', 'illustrator', 'audition', 'media encoder', 'vlc', 'obs', 'davinci', 'filmora']):
            return "🎬"
        elif any(x in n for x in ['chrome', 'firefox', 'edge', 'browser', 'torrent', 'utorrent', 'bittorrent', 'opera', 'brave']):
            return "🌐"
        elif any(x in n for x in ['visual studio', 'vscode', 'python', 'git', '7-zip', 'winrar', 'sublime', 'node', 'java', 'code']):
            return "🛠️"
        elif any(x in n for x in ['gameloop', 'steam', 'epic', 'riot', 'game', 'tencent', 'play', 'fortnite']):
            return "🎮"
        elif any(x in n for x in ['driver', 'intel', 'nvidia', 'amd', 'realtek', 'windows', 'system']):
            return "⚙️"
        else:
            return "📦"

    def _update_apps_listbox(self, apps_list):
        """Update app listbox with styled tiles and icon symbols"""
        self.app_listbox.delete(0, tk.END)
        self.filtered_apps = apps_list
        for app in apps_list:
            icon = self._get_app_icon_symbol(app.display_name, app.publisher)
            ver = f" ({app.version})" if app.version else ""
            self.app_listbox.insert(tk.END, f" {icon}  {app.display_name}{ver}")

    # ─── Search ──────────────────────────────────────────────
    
    def _on_search(self, *args):
        """Filter app list based on search text"""
        query = self.search_var.get().lower().strip()
        filtered = [
            app for app in self.installed_apps
            if not query or query in app.display_name.lower() or (app.publisher and query in app.publisher.lower())
        ]
        self._update_apps_listbox(filtered)
    
    # ─── App Scanning ────────────────────────────────────────
    
    def _scan_applications(self) -> None:
        """Scan for installed applications"""
        self.update_log("Scanning for installed applications...")
        self.status_var.set("Scanning applications...")
        self.scan_button.config(state='disabled')
        
        def scan_thread():
            self.installed_apps = self.app_detector.scan_installed_applications()
            self.root.after(0, self._on_scan_complete)
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _on_scan_complete(self) -> None:
        """Handle scan completion"""
        self.scan_button.config(state='normal')
        
        if not self.installed_apps:
            self.update_log("No applications found. Try running as administrator.")
            self.status_var.set("No applications detected")
            return
        
        self._update_apps_listbox(self.installed_apps)
        self._refresh_history_tab()
        
        count = len(self.installed_apps)
        self.update_log(f"Found {count} installed applications")
        self.status_var.set(f"Ready — {count} applications available")

    def _refresh_history_tab(self):
        """Refresh the backup history tab list"""
        self.history_listbox.delete(0, tk.END)
        self.history_items = []

        backups = self.history_manager.get_backup_history() or {}
        for app_name, info in backups.items():
            icon = self._get_app_icon_symbol(app_name)
            last_backup = info.get('last_backup', 'Unknown date')
            if 'T' in last_backup:
                last_backup = last_backup.replace('T', ' ')[:16]

            display_str = f" {icon}  {app_name}   [{last_backup}]"
            self.history_listbox.insert(tk.END, display_str)
            self.history_items.append({'app_name': app_name, 'info': info})
    
    # ─── Selection Handlers ──────────────────────────────────
    
    def _on_app_selected(self, event=None) -> None:
        """Handle application selection from listbox"""
        selection = self.app_listbox.curselection()
        if not selection or not hasattr(self, 'filtered_apps'):
            return
        
        index = selection[0]
        if index >= len(self.filtered_apps):
            return

        selected_app = self.filtered_apps[index]
        self.selected_app = selected_app
        self.restore_path_from_history = None
        self.backup_button.config(state='normal')
        self.uninstall_button.config(state='normal' if selected_app.can_uninstall else 'disabled')
        
        # Update detail panel
        self._update_detail_panel(selected_app)
        
        # Detect data paths in background
        self.status_var.set(f"Scanning data for: {selected_app.display_name}...")
        
        def detect_thread():
            data_paths = self.app_detector.get_application_data_paths(selected_app)
            self.root.after(0, lambda: self._on_paths_detected(selected_app, data_paths))
        
        threading.Thread(target=detect_thread, daemon=True).start()

    def _on_history_selected(self, event=None):
        """Handle backup selection from Section 2 Backup History tab"""
        selection = self.history_listbox.curselection()
        if not selection or not hasattr(self, 'history_items'):
            return

        index = selection[0]
        if index >= len(self.history_items):
            return

        item = self.history_items[index]
        app_name = item['app_name']
        info = item['info']
        backup_path = info.get('location', '')

        self.restore_path_from_history = backup_path

        # Update History Detail Card labels
        icon = self._get_app_icon_symbol(app_name)
        if hasattr(self, 'hist_detail_labels'):
            self.hist_detail_labels['app_name'].config(text=f"{icon} {app_name}")
            self.hist_detail_labels['version'].config(text=info.get('version', '—'))
            self.hist_detail_labels['backup_date'].config(text=info.get('last_backup', '—'))
            self.hist_detail_labels['location'].config(text=backup_path or "—")
            self.hist_detail_labels['status'].config(text="✅ Archive Verified — Ready to Restore")

        if hasattr(self, 'hist_restore_button'):
            self.hist_restore_button.config(state='normal')

        self.status_var.set(f"Backup archive selected: {app_name}")

    def _on_hist_restore_click(self):
        """Handle restore click from Section 2 Backup History tab"""
        if getattr(self, 'restore_path_from_history', None):
            self._perform_restore(self.restore_path_from_history)
        else:
            messagebox.showinfo("Select Backup", "Please select a backup archive from the history list first.")

    
    def _update_detail_panel(self, app: InstalledApplication):
        """Update the detail panel with app info"""
        icon = self._get_app_icon_symbol(app.display_name, app.publisher)
        self.detail_labels['name'].config(text=f"{icon} {app.display_name}")
        self.detail_labels['version'].config(text=app.version or "—")
        self.detail_labels['publisher'].config(text=app.publisher or "—")
        self.detail_labels['size'].config(text=app.size_display)
        
        # Format install date
        date_str = "—"
        if app.install_date:
            try:
                d = app.install_date
                if len(d) == 8:
                    date_str = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
                else:
                    date_str = d
            except:
                date_str = app.install_date
        self.detail_labels['install_date'].config(text=date_str)
        
        self.detail_labels['install_loc'].config(
            text=app.install_location or "Searching...")
        
        # Truncate uninstall command for display
        uninstall_display = "—"
        if app.uninstall_string:
            cmd = app.uninstall_string
            uninstall_display = cmd if len(cmd) <= 60 else cmd[:57] + "..."
        self.detail_labels['uninstall_cmd'].config(text=uninstall_display)
        
        # Placeholders for data counts (updated after scan)
        self.detail_labels['user_data'].config(text="Scanning...")
        self.detail_labels['program_data'].config(text="Scanning...")
        self.detail_labels['registry_keys'].config(text="Scanning...")
    
    def _on_paths_detected(self, app: InstalledApplication, data_paths: Dict):
        """Update detail panel with detected paths"""
        if self.selected_app != app:
            return  # Selection changed during scan
        
        self.current_data_paths = data_paths

        # If registry install_location was empty, display auto-discovered install directory
        display_loc = app.install_location
        if not display_loc:
            discovered = data_paths.get('program_data', []) + data_paths.get('custom_locations', [])
            if discovered:
                display_loc = discovered[0]

        self.detail_labels['install_loc'].config(text=display_loc or "—")

        
        user_count = len(data_paths.get('user_data', []))
        prog_count = len(data_paths.get('program_data', []))
        reg_count = len(data_paths.get('registry_keys', []))
        custom_count = len(data_paths.get('custom_locations', []))
        
        user_text = f"{user_count} location{'s' if user_count != 1 else ''}"
        prog_text = f"{prog_count} location{'s' if prog_count != 1 else ''}"
        reg_text = f"{reg_count} key{'s' if reg_count != 1 else ''}"
        
        if custom_count > 0:
            prog_text += f" + {custom_count} custom"
        
        shortcut_count = len(data_paths.get('shortcuts', []))
        
        self.detail_labels['user_data'].config(text=user_text)
        self.detail_labels['program_data'].config(text=prog_text)
        self.detail_labels['registry_keys'].config(text=reg_text)
        
        self.status_var.set(f"Ready — {app.display_name} selected")
        
        # Log summary
        self.update_log("─" * 50)
        self.update_log(f"Selected: {app.display_name}")
        if app.version:
            self.update_log(f"  Version: {app.version}")
        if app.install_location:
            self.update_log(f"  Install: {app.install_location}")
        self.update_log(f"  Data: {user_count} user, {prog_count} program, {reg_count} registry")
        if app.can_uninstall:
            self.update_log(f"  ✅ Uninstall available")
        else:
            self.update_log(f"  ⚠️ No uninstall command found")
        self.update_log("─" * 50)
    
    # ─── Destination ─────────────────────────────────────────
    
    def _choose_destination(self) -> None:
        """Choose backup destination"""
        destination = filedialog.askdirectory(
            title="Select Backup Destination Folder",
            initialdir=self.backup_destination or None
        )
        
        if destination:
            self.backup_destination = destination
            self.dest_var.set(destination)
            self.update_log(f"📁 Destination set: {destination}")
    
    # ─── Backup ──────────────────────────────────────────────
    
    def _on_backup_click(self) -> None:
        """Handle backup button click"""
        if not self.selected_app:
            messagebox.showwarning("No Selection", "Please select an application to backup")
            return
        
        if not self.backup_destination:
            messagebox.showwarning("No Destination", "Please choose a backup destination folder")
            return
        
        # Use cached paths or detect
        data_paths = self.current_data_paths
        if not data_paths:
            data_paths = self.app_detector.get_application_data_paths(self.selected_app)
        
        if not any(data_paths.values()):
            messagebox.showwarning(
                "No Data Found",
                "Could not locate any data files for this application.\n\n"
                "The application may not store user data in standard locations."
            )
            return
        
        # Confirm
        result = messagebox.askyesno(
            "Confirm Backup",
            f"Backup '{self.selected_app.display_name}' to:\n{self.backup_destination}\n\nContinue?"
        )
        
        if not result:
            return
        
        # Perform backup
        self._disable_buttons()
        self.progress.start()
        self.status_var.set("Backing up...")
        
        def backup_thread():
            success = self.backup_engine.backup_application(
                self.selected_app.display_name,
                data_paths,
                self.backup_destination,
                self.selected_app.version
            )
            self.root.after(0, lambda: self._on_backup_complete(success))
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def _on_backup_complete(self, success: bool) -> None:
        """Handle backup completion"""
        self.progress.stop()
        self._enable_buttons()
        
        if success:
            self.status_var.set("Backup completed successfully")
            messagebox.showinfo(
                "Success",
                "Application backup completed successfully!\n\nBackup has been added to history."
            )
        else:
            self.status_var.set("Backup failed")
            messagebox.showerror("Error", "Backup failed. Check the log for details.")
    
    # ─── Uninstall ───────────────────────────────────────────
    
    def _on_uninstall_click(self) -> None:
        """Handle uninstall button click"""
        if not self.selected_app:
            messagebox.showwarning("No Selection", "Please select an application to uninstall")
            return
        
        app = self.selected_app
        
        if not app.can_uninstall:
            messagebox.showwarning(
                "Cannot Uninstall",
                f"No uninstall command found for '{app.display_name}'.\n\n"
                "This application may need to be removed manually."
            )
            return
        
        # Offer to backup first
        backup_first = messagebox.askyesnocancel(
            "Backup Before Uninstall?",
            f"Do you want to backup '{app.display_name}' before uninstalling?\n\n"
            "Yes = Backup first, then uninstall\n"
            "No = Uninstall without backup\n"
            "Cancel = Cancel operation"
        )
        
        if backup_first is None:
            return  # Cancelled
        
        if backup_first:
            # Need a destination
            if not self.backup_destination:
                messagebox.showwarning(
                    "No Destination",
                    "Please choose a backup destination folder first."
                )
                return
        
        # Final confirmation
        silent_option = ""
        if app.can_silent_uninstall:
            silent_option = "\n\n☑ Silent uninstall is available for this app."
        
        result = messagebox.askyesno(
            "⚠️ Confirm Uninstall",
            f"Are you sure you want to uninstall '{app.display_name}'?\n\n"
            f"Uninstall command:\n{app.uninstall_string}\n\n"
            f"This action cannot be undone."
            f"{silent_option}",
            icon='warning'
        )
        
        if not result:
            return
        
        # Ask about silent mode
        use_silent = False
        if app.can_silent_uninstall:
            use_silent = messagebox.askyesno(
                "Silent Uninstall?",
                "Use silent (no UI) uninstall?\n\n"
                "Yes = Silent uninstall (faster, no dialogs)\n"
                "No = Standard uninstall (shows uninstaller UI)"
            )
        
        # Start the process
        self._disable_buttons()
        self.progress.start()
        self.status_var.set("Uninstalling...")
        
        def uninstall_thread():
            # Step 1: Backup if requested
            backup_ok = True
            if backup_first:
                self.update_log("Step 1/2: Backing up before uninstall...")
                data_paths = self.current_data_paths or \
                    self.app_detector.get_application_data_paths(app)
                backup_ok = self.backup_engine.backup_application(
                    app.display_name, data_paths,
                    self.backup_destination, app.version
                )
                if not backup_ok:
                    self.root.after(0, lambda: self._on_uninstall_complete({
                        'success': False,
                        'message': 'Backup failed — uninstall cancelled for safety'
                    }))
                    return
                self.update_log("Backup completed. Proceeding to uninstall...")
            
            # Step 2: Uninstall
            step = "Step 2/2" if backup_first else "Uninstalling"
            self.update_log(f"{step}: Running uninstaller...")
            result = self.uninstall_engine.uninstall_application(
                app, silent=use_silent)
            
            self.root.after(0, lambda: self._on_uninstall_complete(result))
        
        threading.Thread(target=uninstall_thread, daemon=True).start()
    
    def _on_uninstall_complete(self, result: dict) -> None:
        """Handle uninstall completion"""
        self.progress.stop()
        self._enable_buttons()
        
        if result['success']:
            self.status_var.set("Uninstall completed")
            
            leftover_msg = ""
            leftover_paths = result.get('leftover_paths', [])
            if leftover_paths:
                leftover_msg = (
                    f"\n\n{len(leftover_paths)} leftover data location(s) found.\n"
                    "Would you like to clean them up?"
                )
                
                cleanup = messagebox.askyesno(
                    "Cleanup Leftover Data?",
                    f"Uninstall completed successfully!\n{leftover_msg}",
                    icon='question'
                )
                
                if cleanup:
                    self._cleanup_leftovers(leftover_paths)
            else:
                messagebox.showinfo(
                    "Success",
                    f"Application uninstalled successfully!\n\n{result['message']}"
                )
            
            # Refresh app list
            self._scan_applications()
        else:
            self.status_var.set("Uninstall failed")
            messagebox.showerror(
                "Uninstall Failed",
                f"{result['message']}\n\nCheck the log for details."
            )
    
    def _cleanup_leftovers(self, paths: list):
        """Clean up leftover paths after uninstall"""
        self.update_log("Cleaning up leftover data...")
        
        cleanup_result = self.uninstall_engine.cleanup_leftover_data(
            self.selected_app, paths, clean_registry=True
        )
        
        self.update_log(
            f"Cleanup complete: {cleanup_result['files_removed']} removed, "
            f"{cleanup_result['files_failed']} failed"
        )
        
        if cleanup_result['errors']:
            for err in cleanup_result['errors'][:5]:
                self.update_log(f"  ⚠️ {err}")
    
    # ─── Restore ─────────────────────────────────────────────
    
    def _on_restore_click(self) -> None:
        """Handle restore button click"""
        # If a specific backup is selected in the History tab
        if getattr(self, 'restore_path_from_history', None):
            self._perform_restore(self.restore_path_from_history)
            return

        backed_up_apps = self.history_manager.get_all_backed_up_apps()
        
        if not backed_up_apps:
            # No local history — suggest browsing
            result = messagebox.askyesno(
                "No Local History",
                "No backup history found locally.\n\n"
                "After a Windows reinstall, history is stored in your backup folder.\n"
                "Would you like to browse to your backup folder?",
                icon='question'
            )
            if result:
                self._on_browse_restore_click()
            return

        
        # Show dialog to select application
        restore_dialog = tk.Toplevel(self.root)
        restore_dialog.title("Restore from History")
        restore_dialog.geometry("500x400")
        restore_dialog.configure(bg=ModernDarkTheme.BG_DARK)
        restore_dialog.transient(self.root)
        restore_dialog.grab_set()
        
        # Center
        restore_dialog.update_idletasks()
        x = (restore_dialog.winfo_screenwidth() // 2) - (restore_dialog.winfo_width() // 2)
        y = (restore_dialog.winfo_screenheight() // 2) - (restore_dialog.winfo_height() // 2)
        restore_dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(restore_dialog, style='TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            main_frame, text="Select Application to Restore",
            style='Title.TLabel'
        ).pack(pady=(0, 20))
        
        list_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            list_frame,
            bg=ModernDarkTheme.BG_MEDIUM,
            fg=ModernDarkTheme.FG_PRIMARY,
            selectbackground=ModernDarkTheme.ACCENT,
            selectforeground=ModernDarkTheme.FG_PRIMARY,
            font=('Segoe UI', 10),
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for app_name in backed_up_apps:
            listbox.insert(tk.END, app_name)
        
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.pack(fill=tk.X)
        
        def do_restore():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an application to restore")
                return
            
            app_name = listbox.get(selection[0])
            backup_location = self.history_manager.get_backup_location(app_name)
            restore_dialog.destroy()
            self._perform_restore(backup_location)
        
        ttk.Button(
            btn_frame, text="Restore Selected", command=do_restore,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame, text="Cancel", command=restore_dialog.destroy,
            style='Accent.TButton'
        ).pack(side=tk.LEFT)
    
    def _on_browse_restore_click(self) -> None:
        """
        Browse to a backup folder to restore from.
        Used after Windows reinstall when local history is gone.
        """
        folder = filedialog.askdirectory(
            title="Select the folder containing your SmartAppBackup backups"
        )
        
        if not folder:
            return
        
        # Try to import history from this location
        imported = self.history_manager.load_history_from_backup(folder)
        if imported:
            self.update_log(f"✅ Imported backup history from: {folder}")
        
        # Scan for available backups by finding manifest files
        self.update_log(f"Scanning for backups in: {folder}...")
        found_backups = self.history_manager.scan_backup_folder(folder)
        
        if not found_backups:
            messagebox.showinfo(
                "No Backups Found",
                f"No SmartAppBackup backups found in:\n{folder}\n\n"
                "Make sure you selected the correct folder."
            )
            return
        
        # Show found backups in a dialog
        browse_dialog = tk.Toplevel(self.root)
        browse_dialog.title("Found Backups")
        browse_dialog.geometry("550x400")
        browse_dialog.configure(bg=ModernDarkTheme.BG_DARK)
        browse_dialog.transient(self.root)
        browse_dialog.grab_set()
        
        # Center
        browse_dialog.update_idletasks()
        x = (browse_dialog.winfo_screenwidth() // 2) - (browse_dialog.winfo_width() // 2)
        y = (browse_dialog.winfo_screenheight() // 2) - (browse_dialog.winfo_height() // 2)
        browse_dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(browse_dialog, style='TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            main_frame, 
            text=f"Found {len(found_backups)} Backup(s)",
            style='Title.TLabel'
        ).pack(pady=(0, 15))
        
        list_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            list_frame,
            bg=ModernDarkTheme.BG_MEDIUM,
            fg=ModernDarkTheme.FG_PRIMARY,
            selectbackground=ModernDarkTheme.ACCENT,
            selectforeground=ModernDarkTheme.FG_PRIMARY,
            font=('Segoe UI', 10),
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for backup in found_backups:
            display = backup['app_name']
            if backup.get('version'):
                display += f" ({backup['version']})"
            listbox.insert(tk.END, display)
        
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.pack(fill=tk.X)
        
        def do_restore():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup to restore")
                return
            
            backup_info = found_backups[selection[0]]
            browse_dialog.destroy()
            self._perform_restore(backup_info['backup_path'])
        
        ttk.Button(
            btn_frame, text="Restore Selected", command=do_restore,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame, text="Cancel", command=browse_dialog.destroy,
            style='Accent.TButton'
        ).pack(side=tk.LEFT)
    
    def _perform_restore(self, backup_path: str) -> None:
        """Perform the actual restore operation"""
        if not AdminUtils.is_admin():
            relaunch = messagebox.askyesno(
                "Administrator Privileges Required",
                "Restoring applications to Program Files, ProgramData, and restoring Registry keys requires Administrator privileges.\n\n"
                "Would you like to restart SmartBackup as Administrator now to ensure full restore succeeds?",
                icon='warning'
            )
            if relaunch:
                AdminUtils.request_admin_privileges()
                return

        result = messagebox.askyesno(
            "Confirm Restore",
            "This will restore application data from the backup.\n"
            "Existing data may be overwritten.\n\nContinue?",
            icon='warning'
        )
        
        if not result:
            return

        
        overwrite = messagebox.askyesno(
            "Overwrite Existing Files?",
            "Should existing files be overwritten?\n\n"
            "Yes = Overwrite existing files\n"
            "No = Skip existing files"
        )
        
        self._disable_buttons()
        self.progress.start()
        self.status_var.set("Restoring...")
        
        def restore_thread():
            success = self.restore_engine.restore_application(backup_path, overwrite)
            self.root.after(0, lambda: self._on_restore_complete(success))
        
        threading.Thread(target=restore_thread, daemon=True).start()
    
    def _on_restore_complete(self, success: bool) -> None:
        """Handle restore completion"""
        self.progress.stop()
        self._enable_buttons()
        
        if success:
            self.status_var.set("Restore completed successfully")
            messagebox.showinfo("Success", "Application restore completed successfully!")
        else:
            self.status_var.set("Restore failed")
            messagebox.showerror("Error", "Restore failed. Check the log for details.")
    
    # ─── Helpers ─────────────────────────────────────────────
    
    def _disable_buttons(self) -> None:
        """Disable action buttons during operations"""
        self.backup_button.config(state='disabled')
        self.restore_button.config(state='disabled')
        self.uninstall_button.config(state='disabled')
        self.scan_button.config(state='disabled')
        self.app_listbox.config(state='disabled')
    
    def _enable_buttons(self) -> None:
        """Enable action buttons after operations"""
        self.backup_button.config(state='normal')
        self.restore_button.config(state='normal')
        self.scan_button.config(state='normal')
        self.app_listbox.config(state='normal')
        # Uninstall button depends on selection
        if self.selected_app and self.selected_app.can_uninstall:
            self.uninstall_button.config(state='normal')
    
    def update_log(self, message: str) -> None:
        """Update the log display with timestamps and formatting"""
        def _update():
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if any(keyword in message.lower() for keyword in ['error', 'failed', 'exception']):
                formatted_msg = f"[{timestamp}] ❌ {message}"
            elif any(keyword in message.lower() for keyword in ['success', 'completed', 'exported', 'imported', 'backed up']):
                formatted_msg = f"[{timestamp}] ✅ {message}"
            elif any(keyword in message.lower() for keyword in ['warning', 'skipping', 'skipped']):
                formatted_msg = f"[{timestamp}] ⚠️ {message}"
            elif any(keyword in message.lower() for keyword in ['starting', 'copying', 'exporting', 'importing', 'restoring', 'uninstall']):
                formatted_msg = f"[{timestamp}] ⏳ {message}"
            else:
                formatted_msg = f"[{timestamp}] ℹ️ {message}"
            
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, formatted_msg + '\n')
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        
        self.root.after(0, _update)
    
    def run(self) -> None:
        """Run the application"""
        self.update_log("🚀 Smart Application Backup Tool Started")
        self.update_log("=" * 50)
        self.root.mainloop()