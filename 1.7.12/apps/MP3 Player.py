from m5stack import *
from m5ui import *
from uiflow import *
import audio
import os
import random
import time

# ---------- CONFIG ----------
MUSIC_DIR = "/sd/music"
VISIBLE_ROWS = 6
BAR_COUNT = 24
SCREEN_W = 240
SCREEN_H = 135
# --------------------------

player = audio.Player()
screen_on = True
search_mode = False
search_text = ""

playlist = []
filtered = []
cursor = 0
scroll = 0

# ---------- DISPLAY ----------
def header():
    lcd.fillRect(0, 0, SCREEN_W, 18, lcd.BLACK)
    lcd.setTextColor(lcd.WHITE)
    lcd.drawString("Cardputer MP3", 5, 4)
    lcd.drawRightString("SEARCH" if search_mode else "", SCREEN_W - 4, 4)

def search_bar():
    lcd.fillRect(0, 18, SCREEN_W, 14, lcd.BLACK)
    if search_mode:
        lcd.drawString(">" + search_text, 5, 20)
    else:
        lcd.drawString("ENTER=Play  /=Search", 5, 20)

def draw_list():
    lcd.fillRect(0, 32, SCREEN_W, 66, lcd.BLACK)
    for i in range(VISIBLE_ROWS):
        idx = scroll + i
        if idx >= len(filtered):
            return
        name = filtered[idx].split("/")[-1][:28]
        y = 34 + i * 11
        prefix = ">" if idx == cursor else " "
        lcd.drawString(prefix + name, 5, y)

def draw_wave():
    if not player.isPlaying():
        return
    lcd.fillRect(0, 98, SCREEN_W, 37, lcd.BLACK)
    bar_w = SCREEN_W // BAR_COUNT
    for i in range(BAR_COUNT):
        h = random.randint(4, 34)
        lcd.fillRect(i * bar_w, 135 - h, bar_w - 2, h, lcd.GREEN)

def redraw():
    header()
    search_bar()
    draw_list()

# ---------- FILES ----------
def load_music():
    global playlist, filtered
    files = []
    for f in os.listdir(MUSIC_DIR):
        if f.lower().endswith(".mp3"):
            path = MUSIC_DIR + "/" + f
            ts = os.stat(path)[8]
            files.append((path, ts))
    files.sort(key=lambda x: x[1], reverse=True)
    playlist = [f[0] for f in files]
    filtered = playlist[:]

def apply_search():
    global filtered, cursor, scroll
    filtered = [p for p in playlist if search_text.lower() in p.lower()]
    cursor = 0
    scroll = 0

# ---------- PLAYBACK ----------
def play_selected():
    if not filtered:
        return
    player.stop()
    player.play(filtered[cursor])

def toggle_play():
    if player.isPlaying():
        player.pause()
    else:
        player.resume()

def stop_play():
    player.stop()

def next_track():
    global cursor
    if not filtered:
        return
    cursor = (cursor + 1) % len(filtered)
    play_selected()
    auto_scroll()

def prev_track():
    global cursor
    if not filtered:
        return
    cursor = (cursor - 1) % len(filtered)
    play_selected()
    auto_scroll()

# ---------- SCROLL ----------
def auto_scroll():
    global scroll
    if cursor < scroll:
        scroll = cursor
    elif cursor >= scroll + VISIBLE_ROWS:
        scroll = cursor - VISIBLE_ROWS + 1

# ---------- SCREEN ----------
def toggle_screen():
    global screen_on
    screen_on = not screen_on
    if not screen_on:
        lcd.clear()
    else:
        redraw()

# ---------- KEYBOARD ----------
def on_key(k):
    global cursor, scroll, search_mode, search_text

    if k == "up":
        cursor = max(cursor - 1, 0)
        auto_scroll()

    elif k == "down":
        cursor = min(cursor + 1, len(filtered) - 1)
        auto_scroll()

    elif k == "left":
        cursor = max(cursor - VISIBLE_ROWS, 0)
        auto_scroll()

    elif k == "right":
        cursor = min(cursor + VISIBLE_ROWS, len(filtered) - 1)
        auto_scroll()

    elif k == "enter":
        if search_mode:
            apply_search()
            search_mode = False
        else:
            play_selected()

    elif k == "escape":
        if search_mode:
            search_mode = False
            search_text = ""
            filtered = playlist[:]
        else:
            stop_play()

    elif k == "/":
        search_mode = not search_mode
        search_text = ""

    elif k == "p" and not search_mode:
        toggle_play()

    elif k == "n" and not search_mode:
        next_track()

    elif k == "b" and not search_mode:
        prev_track()

    elif k == "s" and not search_mode:
        toggle_screen()

    elif search_mode:
        if k == "backspace":
            search_text = search_text[:-1]
        elif len(k) == 1 and k.isalnum():
            search_text += k

    redraw()

keyboard.event(on_key)

# ---------- MAIN ----------
load_music()
redraw()

while True:
    if screen_on:
        draw_wave()
    wait_ms(60)
