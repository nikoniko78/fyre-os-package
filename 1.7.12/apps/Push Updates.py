import urequests
import uos
import time
from m5stack import lcd
from machine import reset

# ------------------------
# CONFIG
# ------------------------
GITHUB_API = "https://api.github.com/repos/nikoniko78/fyre-os-package/contents/"
SD_ROOT = "/sd"
TEMP_DIR = "/sd/tmp_update"
MIN_API_CALLS = 5

BAR_WIDTH = 220
BAR_HEIGHT = 20
STEP_BAR_HEIGHT = 10
BAR_X = 60
BAR_Y = 100
STEP_BAR_Y = 140

# ------------------------
# HELPERS
# ------------------------
def version_tuple(v):
    return tuple(int(x) for x in v.split('.'))

def check_api_rate():
    r = urequests.get("https://api.github.com/rate_limit")
    data = r.json()
    r.close()
    return data["rate"]["remaining"]

def get_latest_folder():
    r = urequests.get(GITHUB_API)
    data = r.json()
    r.close()
    max_version = (0,)
    latest_folder_url = None
    for item in data:
        if item["type"] == "dir":
            try:
                v_tuple = version_tuple(item["name"])
                if v_tuple > max_version:
                    max_version = v_tuple
                    latest_folder_url = item["url"]
            except:
                pass
    return latest_folder_url

def show_message_centered(message):
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu24)
    w = lcd.textWidth(message)
    h = lcd.textHeight(message)
    x = (lcd.width() - w) // 2
    y = (lcd.height() - h) // 2
    lcd.text(x, y, message, lcd.WHITE)

def draw_progress(cumulative_progress, total_size):
    """Top bar: cumulative progress across all files."""
    lcd.rect(BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT, lcd.WHITE)  # border
    fill_width = int(BAR_WIDTH * cumulative_progress / total_size)
    lcd.rect(BAR_X, BAR_Y, fill_width, BAR_HEIGHT, lcd.WHITE, True)

def draw_step_progress(current_file, total_files):
    """Bottom bar: file count progress"""
    lcd.rect(BAR_X, STEP_BAR_Y, BAR_WIDTH, STEP_BAR_HEIGHT, lcd.WHITE)
    fill_width = int(BAR_WIDTH * current_file / total_files)
    lcd.rect(BAR_X, STEP_BAR_Y, fill_width, STEP_BAR_HEIGHT, lcd.WHITE, True)

def download_file_to_temp(file_info, cumulative_downloaded, total_size_all):
    """Download single file and update top progress bar cumulatively."""
    try:
        uos.mkdir(TEMP_DIR)
    except:
        pass
    download_url = file_info["download_url"]
    filename = TEMP_DIR + "/" + file_info["name"]
    r = urequests.get(download_url, stream=True)
    file_total = int(r.headers.get("Content-Length", 0))
    downloaded = 0
    chunk_size = 512
    with open(filename, "wb") as f:
        while True:
            chunk = r.raw.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            draw_progress(cumulative_downloaded + downloaded, total_size_all)
    r.close()
    return file_total  # return size downloaded

def apply_update():
    for fname in uos.listdir(TEMP_DIR):
        src = TEMP_DIR + "/" + fname
        dst = SD_ROOT + "/" + fname
        try:
            uos.remove(dst)
        except:
            pass
        uos.rename(src, dst)
    uos.rmdir(TEMP_DIR)

# ------------------------
# MAIN UPDATER
# ------------------------
def update_sd():
    remaining_calls = check_api_rate()
    if remaining_calls < MIN_API_CALLS:
        show_message_centered(f"Too few API calls: {remaining_calls}")
        return

    latest_folder_url = get_latest_folder()
    if not latest_folder_url:
        show_message_centered("No update folders found.")
        return

    r = urequests.get(latest_folder_url)
    files = [f for f in r.json() if f["type"] == "file"]
    r.close()

    total_files = len(files)
    total_size_all = 0
    # Pre-calculate total size for cumulative progress
    for f in files:
        r = urequests.get(f["download_url"], stream=True)
        total_size_all += int(r.headers.get("Content-Length", 0))
        r.close()

    cumulative_downloaded = 0
    lcd.clear()
    lcd.font(lcd.FONT_Default)

    current_file = 0
    for f in files:
        current_file += 1
        draw_step_progress(current_file - 1, total_files)
        file_size = download_file_to_temp(f, cumulative_downloaded, total_size_all)
        cumulative_downloaded += file_size
        draw_step_progress(current_file, total_files)

    apply_update()
    show_message_centered("Update Complete.\nThe system will restart momentarily.")
    time.sleep(3)
    reset()

# ------------------------
# RUN UPDATER
# ------------------------
update_sd()
