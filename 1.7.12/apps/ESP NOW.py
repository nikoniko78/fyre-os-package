# espnow_chat.py
from m5stack import *
from m5ui import *
from uiflow import *
import espnow
import ujson
import _thread
import os

# ----------------------------------------------------
# Files
# ----------------------------------------------------
NICKNAME_FILE = "/sd/espnow_nickname.json"

# ----------------------------------------------------
# Setup screen
# ----------------------------------------------------
setScreenColor(0x222222)
lcd.clear()
lcd.font(lcd.FONT_DejaVu18)
lcd.text(10, 5, "ESP-NOW Chat", 0xFFFFFF)

# ----------------------------------------------------
# Load or set nickname
# ----------------------------------------------------
if os.path.exists(NICKNAME_FILE):
    with open(NICKNAME_FILE, "r") as f:
        nickname = ujson.load(f).get("nickname", "Me")
else:
    # First time: ask for nickname
    from uiflow import inputBox
    nickname = inputBox("Enter nickname:", "")
    if not nickname:
        nickname = "Me"
    with open(NICKNAME_FILE, "w") as f:
        ujson.dump({"nickname": nickname}, f)

# ----------------------------------------------------
# Chat display area
# ----------------------------------------------------
chat_y_start = 30
chat_lines = []
max_lines = 10

def draw_chat():
    lcd.clear()
    lcd.text(10, 5, "ESP-NOW Chat", 0xFFFFFF)
    y = chat_y_start
    for line in chat_lines[-max_lines:]:
        lcd.text(10, y, line, 0xFFFFFF)
        y += 18

# ----------------------------------------------------
# Input line
# ----------------------------------------------------
input_text = ""
lcd.text(10, 220, "> " + input_text, 0xFFFFFF)

def update_input():
    lcd.fillRect(0, 220, 320, 30, 0x222222)  # clear input line
    lcd.text(10, 220, "> " + input_text, 0xFFFFFF)

# ----------------------------------------------------
# ESP-NOW setup
# ----------------------------------------------------
peer = b'\xff\xff\xff\xff\xff\xff'  # broadcast
esp = espnow.ESPNow()
esp.init()
esp.add_peer(peer)

# ----------------------------------------------------
# Send message
# ----------------------------------------------------
def send_message():
    global input_text
    msg = input_text.strip()
    if msg:
        full_msg = f"{nickname}: {msg}"
        esp.send(peer, full_msg)
        chat_lines.append(full_msg)
        draw_chat()
        input_text = ""
        update_input()

# ----------------------------------------------------
# Receive loop
# ----------------------------------------------------
def recv_loop():
    while True:
        res = esp.recv()
        if res:
            sender, data = res
            chat_lines.append("Peer: " + data.decode())
            draw_chat()
        wait(0.1)

_thread.start_new_thread(recv_loop, ())

# ----------------------------------------------------
# Buttons
# ----------------------------------------------------
def btnA_pressed():
    send_message()

btnA.wasPressed(btnA_pressed)

def btnB_pressed():
    global input_text
    input_text += "B"  # demo input
    update_input()

btnB.wasPressed(btnB_pressed)

def btnC_pressed():
    global input_text
    input_text += "C"  # demo input
    update_input()

btnC.wasPressed(btnC_pressed)

# ----------------------------------------------------
# Keyboard typing
# ----------------------------------------------------
def on_key(key):
    global input_text
    if key == "\n":
        send_message()
    elif key == "\b":
        input_text = input_text[:-1]
    else:
        input_text += key
    update_input()

setKeyCallback(on_key)

# ----------------------------------------------------
# Main loop
# ----------------------------------------------------
while True:
    wait(0.1)
