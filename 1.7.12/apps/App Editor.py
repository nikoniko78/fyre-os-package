from m5stack import *
from m5ui import *
from uiflow import *
import os

# ------------------------------
# UI Setup
# ------------------------------
setScreenColor(0x000000)  # black background
lcd.setTextColor(0xFFFFFF, 0x000000)

# Colors
KEYWORD_COLOR = 0x00FF00
STRING_COLOR = 0xFFFF00
COMMENT_COLOR = 0x888888
CURSOR_COLOR = 0xFF0000

# ------------------------------
# Scan for Python files
# ------------------------------
py_files = []

def scan_py_files(path="/sd"):
    global py_files
    py_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

scan_py_files()

# ------------------------------
# Editor state
# ------------------------------
selected_file_idx = 0
lines = []
cursor_x = 0
cursor_y = 0
scroll_y = 0
file_path = ""

# ------------------------------
# Load / Save
# ------------------------------
def load_file(path):
    global lines
    try:
        with open(path, "r") as f:
            lines = f.read().splitlines()
    except:
        lines = [""]

def save_file():
    global file_path, lines
    try:
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
    except:
        pass

# ------------------------------
# Syntax Highlighting (simple)
# ------------------------------
keywords = ["def", "class", "import", "from", "for", "while", "if", "else", "elif", "return"]

def draw_editor():
    lcd.clear()
    max_lines = 16  # lines visible on screen
    for idx in range(scroll_y, min(scroll_y + max_lines, len(lines))):
        line = lines[idx]
        x = 0
        for word in line.split(" "):
            color = KEYWORD_COLOR if word in keywords else STRING_COLOR if '"' in word or "'" in word else COMMENT_COLOR if word.startswith("#") else 0xFFFFFF
            lcd.print(word + " ", x, (idx - scroll_y) * 15, color)
            x += 8 * (len(word)+1)
    # Draw cursor
    lcd.rect(cursor_x*8, (cursor_y-scroll_y)*15, 8, 15, CURSOR_COLOR)

# ------------------------------
# File Selection
# ------------------------------
def display_file_list():
    lcd.clear()
    lcd.print("Python Files:", 0, 0, 0xFFFFFF)
    for idx, f in enumerate(py_files):
        color = CURSOR_COLOR if idx == selected_file_idx else 0xFFFFFF
        lcd.print(f"  {f}", 0, 20 + idx*15, color)

# ------------------------------
# Main Loop
# ------------------------------
display_file_list()

while True:
    if btnA.isPressed():  # Up
        if file_path:  # in editor
            cursor_y = max(0, cursor_y-1)
            if cursor_y < scroll_y:
                scroll_y -= 1
            draw_editor()
        else:
            selected_file_idx = max(0, selected_file_idx-1)
            display_file_list()
        wait_ms(150)

    if btnB.isPressed():  # Enter / Select
        if not file_path:
            file_path = py_files[selected_file_idx]
            load_file(file_path)
            cursor_x = cursor_y = scroll_y = 0
            draw_editor()
        else:
            save_file()
        wait_ms(150)

    if btnC.isPressed():  # Down
        if file_path:
            cursor_y = min(len(lines)-1, cursor_y+1)
            if cursor_y - scroll_y >= 16:
                scroll_y += 1
            draw_editor()
        else:
            selected_file_idx = min(len(py_files)-1, selected_file_idx+1)
            display_file_list()
        wait_ms(150)
