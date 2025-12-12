import os
import shutil
from m5stack import *
from m5stack_ui import *
from uiflow import *

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)

title = M5Label("System Folder Cleaner", x=10, y=10, color=0xFFFFFF, font=FONT_MONT_22)
info = M5Label("", x=10, y=40, color=0xAAAAAA, font=FONT_MONT_18)

BASE_PATH = "/sd"
CONFIG_FILE = os.path.join(BASE_PATH, "auto_run_config.txt")

# System-generated folders from various OS
SYSTEM_FOLDERS = [
    # Android
    "Android", "DCIM", "Movies", "Pictures", "Alarms",
    "Notifications", "Ringtones", "Podcasts", "Audiobooks", ".thumbnails",
    # Windows
    "System Volume Information", "$RECYCLE.BIN", "Desktop.ini", "Thumbs.db",
    # macOS
    ".DS_Store", ".Spotlight-V100", ".Trashes", ".fseventsd",
    # Linux
    ".Trash-1000", ".directory", ".localized"
]

# Whitelist folders/files to never delete
WHITELIST_FOLDERS = ["Settings", "Apps", "Assets", "Music"]
WHITELIST_EXTENSIONS = [".py"]

# -------------------
# Helper Functions
# -------------------
def is_system_generated(path):
    folder_name = path.split("/")[-1]

    # Skip whitelisted folders
    if folder_name in WHITELIST_FOLDERS:
        return False

    # Skip whitelisted files
    if os.path.isfile(path):
        for ext in WHITELIST_EXTENSIONS:
            if path.endswith(ext):
                return False

    # Name-based detection
    if folder_name in SYSTEM_FOLDERS:
        return True

    # Metadata check: empty or auto-created
    try:
        stat = os.stat(path)
        created = stat[9]
        modified = stat[8]
        if abs(modified - created) < 3:
            return True
    except:
        pass

    # Android-specific structure
    if "/Android/data" in path or "/Android/media" in path:
        return True

    # Empty or minimal contents
    try:
        if os.path.isdir(path):
            contents = os.listdir(path)
            if len(contents) == 0:
                return True
            if len(contents) <= 2 and all(len(os.listdir(os.path.join(path, c))) == 0 for c in contents):
                return True
    except:
        pass

    return False

def scan_sd():
    system_folders_found = []
    for item in os.listdir(BASE_PATH):
        full_path = os.path.join(BASE_PATH, item)
        if is_system_generated(full_path):
            system_folders_found.append(full_path)
    return system_folders_found

def load_auto_run():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip() == "ON"
    return False

def save_auto_run(enabled):
    with open(CONFIG_FILE, "w") as f:
        f.write("ON" if enabled else "OFF")

def delete_folders(folders):
    for f in folders:
        try:
            shutil.rmtree(f)
        except:
            pass

# -------------------
# Main Logic
# -------------------
auto_run_enabled = load_auto_run()

if auto_run_enabled:
    # Auto-run: delete system folders automatically
    system_folders = scan_sd()
    delete_folders(system_folders)
    info.set_text(f"Auto-run active. Deleted {len(system_folders)} system folders (excluding whitelist).")
else:
    # Manual mode: show PSA
    info.set_text("⚠️ PSA: You are responsible for any data loss!")

y_pos = 80
toggle_btn = M5Btn(text=f"Toggle Auto-Run", x=50, y=y_pos, w=220, h=50, bg_c=0x5555AA, text_c=0xFFFFFF)
scan_btn   = M5Btn(text=f"Scan & Clean", x=50, y=y_pos+70, w=220, h=50, bg_c=0x00AA00, text_c=0xFFFFFF)

system_folder_labels = []

def toggle_auto_run():
    global auto_run_enabled
    auto_run_enabled = not auto_run_enabled
    save_auto_run(auto_run_enabled)
    info.set_text(f"Auto-Run on Boot: {'ON' if auto_run_enabled else 'OFF'}")

def scan_and_clean():
    # Clear previous labels
    for lbl in system_folder_labels:
        lbl.set_hidden(True)
    system_folder_labels.clear()

    system_folders = scan_sd()
    if not system_folders:
        info.set_text("No system folders found!")
        return

    info.set_text("System folders detected:")
    y = 150
    for f in system_folders:
        lbl = M5Label(f, x=10, y=y, color=0x22FF22, font=FONT_MONT_16)
        system_folder_labels.append(lbl)
        y += 20

    yes_btn = M5Btn(text="YES", x=50, y=y+20, w=100, h=50, bg_c=0x006600, text_c=0xFFFFFF)
    no_btn  = M5Btn(text="NO",  x=200, y=y+20, w=100, h=50, bg_c=0x660000, text_c=0xFFFFFF)

    def yes_pressed():
        info.set_text("Deleting...")
        delete_folders(system_folders)
        info.set_text("System folders removed (whitelisted folders preserved)!")
        yes_btn.set_hidden(True)
        no_btn.set_hidden(True)
        for lbl in system_folder_labels:
            lbl.set_hidden(True)

    def no_pressed():
        info.set_text("Cancelled.")
        yes_btn.set_hidden(True)
        no_btn.set_hidden(True)

    yes_btn.pressed(yes_pressed)
    no_btn.pressed(no_pressed)

toggle_btn.pressed(toggle_auto_run)
scan_btn.pressed(scan_and_clean)
