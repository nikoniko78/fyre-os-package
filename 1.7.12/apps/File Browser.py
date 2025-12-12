from m5stack import *
from m5ui import *
from uiflow import *
import os
import shutil
import time

# ------------------------------
# UI Setup
# ------------------------------
setScreenColor(0x000000)
lcd.setTextColor(0xFFFFFF, 0x000000)

# ------------------------------
# Variables
# ------------------------------
current_path = "/sd"
selected_idx = 0
files_list = []
copy_buffer = None
cut_item = None
max_display = 16
hidden_files = set()
show_hidden = False
last_dot_time = 0  # For double-tap detection

# ------------------------------
# Helpers
# ------------------------------
def list_dir(path):
    entries = []
    try:
        for f in os.listdir(path):
            if not show_hidden and f.startswith("."):
                continue
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                entries.append(("folder", f))
            else:
                entries.append(("file", f))
        entries.sort(key=lambda x: (x[0], x[1]))
    except:
        pass
    return entries

def draw_file_manager():
    lcd.clear()
    lcd.print("Path: " + current_path, 0, 0, 0xFFFFFF)
    start = max(0, selected_idx - max_display + 1)
    for i, (typ, name) in enumerate(files_list[start:start+max_display]):
        y = 20 + i*15
        icon = ">" if typ=="folder" else "#"
        color = 0xFF0000 if i+start==selected_idx else 0xFFFFFF
        # Gray out if cut
        if cut_item and os.path.join(current_path, name) == cut_item:
            color = 0x888888
        flags = ""
        full_path = os.path.join(current_path, name)
        if not os.access(full_path, os.W_OK):
            flags += " [R]"
        if name.startswith("."):
            flags += " [H]"
        lcd.print(f"{icon} {name}{flags}", 0, y, color)

def refresh_files():
    global files_list
    files_list = list_dir(current_path)
    draw_file_manager()

def delete_file(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except:
        pass

def toggle_writeprotect(path):
    try:
        if os.access(path, os.W_OK):
            os.chmod(path, 0o444)
        else:
            os.chmod(path, 0o666)
    except:
        pass

def copy_file(src, dst):
    try:
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
        else:
            shutil.copy(src, dst)
    except:
        pass

def move_file(src, dst):
    try:
        shutil.move(src, dst)
    except:
        pass

# ------------------------------
# Initial
# ------------------------------
refresh_files()

# ------------------------------
# Main Loop
# ------------------------------
while True:
    wait_ms(50)

    if btnA.isPressed():
        selected_idx = max(0, selected_idx-1)
        draw_file_manager()
        wait_ms(150)
    if btnC.isPressed():
        selected_idx = min(len(files_list)-1, selected_idx+1)
        draw_file_manager()
        wait_ms(150)

    key = kb.getKey()
    if key:
        entry = files_list[selected_idx] if files_list else None

        if key == "ENTER" and entry:
            if entry[0]=="folder":
                current_path = os.path.join(current_path, entry[1])
                selected_idx = 0
                refresh_files()
        elif key == "ESCAPE":
            if current_path != "/sd":
                current_path = os.path.dirname(current_path)
                selected_idx = 0
                refresh_files()
        elif key == "D" and entry:
            delete_file(os.path.join(current_path, entry[1]))
            refresh_files()
        elif key == "W" and entry:
            toggle_writeprotect(os.path.join(current_path, entry[1]))
            refresh_files()
        elif key == "C" and entry:
            copy_buffer = os.path.join(current_path, entry[1])
            cut_item = None
        elif key == "X" and entry:
            full_path = os.path.join(current_path, entry[1])
            if cut_item == full_path:
                cut_item = None
            else:
                cut_item = full_path
                copy_buffer = None
            draw_file_manager()
        elif key == "P" and (copy_buffer or cut_item):
            dst = current_path
            if cut_item:
                move_file(cut_item, dst)
                cut_item = None
            elif copy_buffer:
                copy_file(copy_buffer, dst)
            refresh_files()
        elif key == ".":
            # Double-tap to toggle hidden
            now = time.ticks_ms()
            if now - last_dot_time < 400:  # double-tap within 400ms
                show_hidden = not show_hidden
                refresh_files()
            last_dot_time = now

    # Optional: redraw every loop in case of asynchronous changes
    # draw_file_manager()
