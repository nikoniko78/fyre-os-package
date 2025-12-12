from m5stack import *
from m5ui import *
from uiflow import *
import sys
import io

# ------------------------------
# UI Setup
# ------------------------------
setScreenColor(0x000000)
lcd.setTextColor(0xFFFFFF, 0x000000)

# ------------------------------
# Shell variables
# ------------------------------
history = []
history_idx = -1
input_line = ""
cursor_pos = 0
scroll_y = 0
max_lines = 12  # visible lines on screen
output_lines = []

# Colors
INPUT_COLOR = 0xFFFF00
ERROR_COLOR = 0xFF0000
CURSOR_COLOR = 0xFF0000
OUTPUT_COLOR = 0xFFFFFF

# ------------------------------
# Capture stdout / stderr
# ------------------------------
class StdCatcher(io.StringIO):
    def write(self, s):
        for line in s.split("\n"):
            if line.strip():
                output_lines.append((line, OUTPUT_COLOR))
        super().write(s)

sys.stdout = StdCatcher()
sys.stderr = StdCatcher()

# ------------------------------
# Draw shell
# ------------------------------
def draw_shell():
    lcd.clear()
    # Show output
    start = max(0, len(output_lines) - max_lines)
    for idx, (line, color) in enumerate(output_lines[start:]):
        lcd.print(line, 0, idx*15, color)
    # Show input line
    lcd.print("> " + input_line, 0, max_lines*15, INPUT_COLOR)
    # Cursor
    lcd.rect((2+cursor_pos)*8, max_lines*15, 8, 15, CURSOR_COLOR)

draw_shell()

# ------------------------------
# Execute command
# ------------------------------
def execute_command(cmd):
    try:
        result = eval(cmd)
        if result is not None:
            output_lines.append((str(result), OUTPUT_COLOR))
    except SyntaxError:
        try:
            exec(cmd)
        except Exception as e:
            output_lines.append((str(e), ERROR_COLOR))
    except Exception as e:
        output_lines.append((str(e), ERROR_COLOR))

# ------------------------------
# Main Loop
# ------------------------------
while True:
    wait_ms(50)
    
    # Handle buttons
    global history_idx, input_line, cursor_pos
    if btnA.isPressed():  # Up = previous history
        if history:
            history_idx = max(0, history_idx-1) if history_idx >= 0 else len(history)-1
            input_line = history[history_idx]
            cursor_pos = len(input_line)
            draw_shell()
            wait_ms(150)
    if btnC.isPressed():  # Down = next history
        if history:
            history_idx = (history_idx+1) % len(history) if history_idx >=0 else 0
            input_line = history[history_idx]
            cursor_pos = len(input_line)
            draw_shell()
            wait_ms(150)
    if btnB.isPressed():  # Enter = execute
        if input_line.strip():
            output_lines.append(("> " + input_line, INPUT_COLOR))
            execute_command(input_line)
            history.append(input_line)
            history_idx = len(history)
            input_line = ""
            cursor_pos = 0
            draw_shell()
            wait_ms(150)
    
    # Keyboard input
    key = kb.getKey()
    if key:
        if key == "BACKSPACE":
            if cursor_pos > 0:
                input_line = input_line[:cursor_pos-1] + input_line[cursor_pos:]
                cursor_pos -= 1
        elif key == "LEFT":
            cursor_pos = max(0, cursor_pos-1)
        elif key == "RIGHT":
            cursor_pos = min(len(input_line), cursor_pos+1)
        elif key == "UP":
            if history:
                history_idx = max(0, history_idx-1)
                input_line = history[history_idx]
                cursor_pos = len(input_line)
        elif key == "DOWN":
            if history:
                history_idx = min(len(history)-1, history_idx+1)
                input_line = history[history_idx]
                cursor_pos = len(input_line)
        else:
            input_line = input_line[:cursor_pos] + key + input_line[cursor_pos:]
            cursor_pos += len(key)
        draw_shell()
