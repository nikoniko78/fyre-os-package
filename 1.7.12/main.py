import os
import json
import time
from M5 import *
from M5Stack import Speaker

# -------------------------------------------------------
# Paths
# -------------------------------------------------------
SPLASH = "/sd/assets/splash.png"
LOCKED = "/sd/assets/locked.png"
AUDIO = "/sd/assets/startup.wav"
SETTINGS = "/sd/settings.json"
LOCKCACHE = "/sd/lockstate.json"

SYSTEM_PASSWORD = "jal190413"
MAX_AUDIO_TIME = 5

# -------------------------------------------------------
# Utility: safe file load
# -------------------------------------------------------
def safe_json_load(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

# -------------------------------------------------------
# Load settings
# -------------------------------------------------------
settings = safe_json_load(SETTINGS, {
    "theme": "dark",
    "volume": 5,
    "boot_app": "hmenu.py",
    "brightness": 80
})

# -------------------------------------------------------
# Save/load lock state
# -------------------------------------------------------
def write_lockstate(is_locked):
    data = {"locked": is_locked}
    with open(LOCKCACHE, "w") as f:
        json.dump(data, f)

def read_lockstate():
    data = safe_json_load(LOCKCACHE, {"locked": False})
    return data.get("locked", False)

# -------------------------------------------------------
# Splash fade
# -------------------------------------------------------
def show_splash_fade():
    screen = M5Screen()
    screen.clean()
    if not os.path.exists(SPLASH):
        return
    try:
        screen.drawImage(SPLASH, 0, 0)
        for opacity in range(255, -1, -10):
            screen.fillRectAlpha(0, 0, 10000, 10000, 0x000000, opacity)
            time.sleep(0.02)
    except Exception as e:
        print("Splash error:", e)

# -------------------------------------------------------
# Startup sound
# -------------------------------------------------------
def play_startup_sound():
    if not os.path.exists(AUDIO):
        return
    try:
        Speaker.setVolume(settings.get("volume", 5) * 10)
        Speaker.playWAV(AUDIO, loop=False)
        start = time.time()
        while Speaker.isPlaying():
            if time.time() - start > MAX_AUDIO_TIME:
                Speaker.stop()
                break
            time.sleep(0.05)
    except Exception as e:
        print("Audio error:", e)

# -------------------------------------------------------
# Password prompt
# -------------------------------------------------------
def password_prompt():
    screen = M5Screen()
    screen.clean()
    screen.setCursor(10, 10)
    screen.print("Please enter boot recovery key:")
    typed = ""
    while True:
        key = M5Keyboard.getKey()
        if key:
            if key == "\n":
                if typed == SYSTEM_PASSWORD:
                    write_lockstate(False)
                    return True
                else:
                    typed = ""
                    screen.clean()
                    screen.print("Mismatch")
            else:
                typed += key
                screen.print("*")
        time.sleep(0.05)

# -------------------------------------------------------
# Lock screen on startup
# -------------------------------------------------------
def lock_screen_startup():
    screen = M5Screen()
    screen.clean()

    # Check if RST is being held at startup
    hold_time = 0
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < 1500:
        if M5Btn.pressed():
            hold_time += 50
        else:
            hold_time = 0
        time.sleep(0.05)

    if hold_time >= 1500:
        # RST held → password prompt
        password_prompt()
    else:
        # Show locked.png indefinitely
        while True:
            if os.path.exists(LOCKED):
                try:
                    screen.drawImage(LOCKED, 0, 0)
                except Exception as e:
                    print("Critical System Failure!", e)
            time.sleep(0.5)

# -------------------------------------------------------
# Boot launcher
# -------------------------------------------------------
def launch_boot_app():
    app = settings.get("boot_app", "hmenu.py")
    path = "/sd/" + app
    if os.path.exists(path):
        with open(path, "r") as f:
            code = f.read()
        exec(code)
    else:
        print("Please insert the MicroSD Card. \nYour system cannot function properly \nwithout setup data.")

# -------------------------------------------------------
# Main boot
# -------------------------------------------------------
try:
    M5Screen().setBrightness(settings.get("brightness", 80))
except:
    pass

# Step 1: Password-only lock on startup
if read_lockstate():
    lock_screen_startup()

show_splash_fade()
play_startup_sound()


# Step 2: Launch apps
launch_boot_app()
