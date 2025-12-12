import urequests as requests
import os
from m5stack import *
from m5ui import *
from uiflow import *
from image import Image

setScreenColor(0x111111)

GITHUB_API_ROOT = "https://api.github.com/repos/nikoniko78/fyre-os-apps/contents/"

APPS_DIR = "/sd/apps"
ASSETS_DIR = "/sd/assets"

# Ensure directories exist
for d in [APPS_DIR, ASSETS_DIR]:
    try:
        os.makedirs(d)
    except:
        pass


# ------------------- Menu -------------------
def draw_menu(options, index):
    lcd.clear()
    lcd.print("Fyre-OS Installer/Updater", 5, 5, 0xFFFFFF)
    lcd.print("Select a folder:", 5, 25, 0xAAAAAA)

    y = 50
    for i, name in enumerate(options):
        color = 0x00FF00 if i == index else 0xFFFFFF
        lcd.print(name, 20, y, color)
        y += 20


# ------------------- GitHub -------------------
def get_directory(url):
    try:
        r = requests.get(url)
        data = r.json()
        r.close()
        return data
    except:
        return []


# ------------------- Paths -------------------
def resolve_path(filename):
    lower = filename.lower()
    if lower.endswith(".py"):
        return f"{APPS_DIR}/{filename}"
    if any(lower.endswith(x) for x in ["png", "jpg", "jpeg", "bmp", "gif", "wav", "mp3", "ogg"]):
        return f"{ASSETS_DIR}/{filename}"
    return f"{APPS_DIR}/{filename}"


# ------------------- Download / Update -------------------
def download_file(download_url, filename):
    local_path = resolve_path(filename)
    try:
        r = requests.get(download_url)
        content = r.content
        r.close()
        with open(local_path, "wb") as f:
            f.write(content)
    except:
        print("Failed downloading:", filename)


def update_if_exists(download_url, filename):
    local_path = resolve_path(filename)
    if os.path.exists(local_path):
        download_file(download_url, filename)


# ------------------- Detect app -------------------
def app_exists(appname):
    for f in os.listdir(APPS_DIR):
        if f.lower().startswith(appname.lower()):
            return True
    return False


# ------------------- Delete app -------------------
def delete_app(appname):
    lcd.clear()
    lcd.print("Deleting app:", 5, 5)
    lcd.print(appname, 5, 30, 0xFF3333)

    # Delete apps
    for f in os.listdir(APPS_DIR):
        if f.lower().startswith(appname.lower()):
            try:
                os.remove(f"{APPS_DIR}/{f}")
            except:
                pass

    # Delete assets
    for f in os.listdir(ASSETS_DIR):
        if f.lower().startswith(appname.lower()):
            try:
                os.remove(f"{ASSETS_DIR}/{f}")
            except:
                pass

    lcd.print("App deleted!", 5, 70, 0x00FF00)
    wait_ms(1000)


# ------------------- Icon handling -------------------
def get_icon_url_and_path(api_data):
    main_py = None
    for item in api_data:
        if item["type"] == "file" and item["name"].lower().endswith(".py"):
            main_py = item["name"]
            break
    if not main_py:
        return None, None

    base_name = main_py[:-3]  # strip .py
    for ext in ["png", "jpg", "jpeg", "bmp"]:
        for item in api_data:
            if item["type"] == "file" and item["name"].lower() == f"{base_name}.{ext}":
                local_path = f"{ASSETS_DIR}/{item['name']}"
                return item["download_url"], local_path
    return None, None


def show_icon_from_sd(url, local_path):
    try:
        # Download to assets if not exists
        if not os.path.exists(local_path):
            r = requests.get(url)
            data = r.content
            r.close()
            with open(local_path, "wb") as f:
                f.write(data)

        # Display icon
        lcd.clear()
        lcd.image(40, 20, local_path)

    except:
        lcd.clear()
        lcd.print("No preview available", 5, 20)


# ------------------- Recursive processing -------------------
def process_folder(api_url, installing_new):
    items = get_directory(api_url)
    total = len(items)
    count = 0

    for item in items:
        count += 1
        lcd.clear()
        lcd.print(f"Processing: {item['name']}", 5, 10)
        lcd.print(f"{count}/{total}", 5, 40, 0x00FF00)

        if item["type"] == "file":
            if installing_new:
                download_file(item["download_url"], item["name"])
            else:
                update_if_exists(item["download_url"], item["name"])
        elif item["type"] == "dir":
            process_folder(item["url"], installing_new)


# ------------------- Main -------------------
root_items = get_directory(GITHUB_API_ROOT)
folders = [i["name"] for i in root_items if i["type"] == "dir"]

index = 0
draw_menu(folders, index)

# Menu navigation
while True:
    key = kb.get_key()
    if key == "UP":
        index = (index - 1) % len(folders)
        draw_menu(folders, index)
    if key == "DOWN":
        index = (index + 1) % len(folders)
        draw_menu(folders, index)
    if key in ["ENTER", "RIGHT"]:
        selected = folders[index]
        break

# Fetch folder content
folder_api = get_directory(GITHUB_API_ROOT + selected)

# Show icon
icon_url, icon_path = get_icon_url_and_path(folder_api)
if icon_url and icon_path:
    show_icon_from_sd(icon_url, icon_path)
else:
    lcd.clear()
    lcd.print("No preview available", 5, 20)

# Action menu
lcd.print(selected, 5, 120, 0x00FF00)
lcd.print("ENTER=Install/Update", 5, 150)
lcd.print("LEFT=Delete App", 5, 170)
lcd.print("RIGHT=Cancel", 5, 190)

while True:
    key = kb.get_key()
    if key == "ENTER":  # Install/Update
        break
    if key == "LEFT":   # Delete
        delete_app(selected)
        raise SystemExit
    if key == "RIGHT":
        raise SystemExit

# Install or update
exists = app_exists(selected)
lcd.clear()
if exists:
    lcd.print("Updating app...", 5, 30)
else:
    lcd.print("Installing app...", 5, 30)

process_folder(GITHUB_API_ROOT + selected, not exists)

lcd.clear()
lcd.print("Process complete.", 5, 60, 0x00FF00)
lcd.print("App installed/updated", 5, 90)
