# Cardputer ADV Launcher for UIFlow 2
# Full Tkinter-style fidelity with smooth scroll

import os
import json
import time
import textwrap
from m5stack import lcd, btnA, btnB, btnC
from uiflow import machine
from machine import RTC
import wifiCfg

# ------------------------------
# CONFIG
# ------------------------------
ASSETS_PATH = "/sd/assets"
APPS_PATH = "/sd/apps"
NEW_ICON_NAME = "New App!.png"
DEFAULT_ICON = os.path.join(ASSETS_PATH, "appicon_default.png")
BACKGROUND_IMG = os.path.join(ASSETS_PATH, "backgrounddev.png")

SCREEN_WIDTH = 240
SCREEN_HEIGHT = 135
ICON_SIZE = 50
ICON_PADDING = 5
TEXT_WIDTH = 80
TEXT_MAX_LINES = 3
STATUS_BAR_HEIGHT = 20
OPENED_APPS_FILE = os.path.join(APPS_PATH, "opened_apps.json")
LOCKED_FILE = os.path.join(APPS_PATH, "lockstate.json")

ANIMATION_STEPS = 5
TEXT_FONT_SIZE = 10
HIGHLIGHT_X = 10

# Wi-Fi animation images
WIFI_ANIM_FILES = ["wifi0.png", "wifi1.png", "wifi2.png", "wifi3.png", "wifi4.png"]
CONNECT_ANIM_FILES = ["connect1.png", "connect2.png", "connect3.png", "connect2.png"]
WIFI_LOCKED_FILE = "wifilocked.png"

# Battery images
BATTERY_FILES = ["battery1.png","battery2.png","battery3.png","battery4.png"]
BATTERY_CHARGE_FILE = "batterycharge.png"
BAT_CRIT_FILES = ["batcritanim1.png","batcritanim2.png"]

# ------------------------------
# UTIL
# ------------------------------
def load_json_file(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

def run_python_app(path):
    with open(path, "r") as f:
        code = f.read()
    exec(code, globals())

# ------------------------------
# STATUS BAR
# ------------------------------
class StatusBar:
    def __init__(self):
        # Load images
        self.wifi_images = [os.path.join(ASSETS_PATH, f) for f in WIFI_ANIM_FILES]
        self.connect_images = [os.path.join(ASSETS_PATH, f) for f in CONNECT_ANIM_FILES]
        self.wifi_locked = os.path.join(ASSETS_PATH, WIFI_LOCKED_FILE)
        self.battery_images = [os.path.join(ASSETS_PATH, f) for f in BATTERY_FILES]
        self.battery_charge_image = os.path.join(ASSETS_PATH, BATTERY_CHARGE_FILE)
        self.bat_crit_images = [os.path.join(ASSETS_PATH, f) for f in BAT_CRIT_FILES]

        self.connecting = True
        self.wifi_index = 0
        self.bat_crit_index = 0
        self.battery_level = 50
        self.charging = False

    def draw(self):
        lcd.fillRect(0, 0, SCREEN_WIDTH, STATUS_BAR_HEIGHT, lcd.BLACK)

        # --------------------
        # Wi-Fi
        # --------------------
        wifi_img_path = None
        try:
            sta_if = wifiCfg.getWiFiStatus()  # connected to router? returns dict with rssi
            if not sta_if:
                # Not connected to any Wi-Fi
                self.connecting = True
                wifi_img_path = self.connect_images[self.wifi_index % len(self.connect_images)]
                self.wifi_index += 1
            else:
                self.connecting = False
                # Check internet by simple GET request
                internet_ok = False
                try:
                    import urequests
                    urequests.get("http://clients3.google.com/generate_204", timeout=1)
                    internet_ok = True
                except:
                    internet_ok = False
                if internet_ok:
                    # Show strength bars
                    wifi_strength = min(max(int(sta_if['rssi'] / -20), 0), 4)
                    wifi_img_path = self.wifi_images[wifi_strength]
                else:
                    # Connected to router but no internet
                    wifi_img_path = self.wifi_locked
        except:
            # fallback
            self.connecting = True
            wifi_img_path = self.connect_images[self.wifi_index % len(self.connect_images)]
            self.wifi_index += 1

        if wifi_img_path and os.path.exists(wifi_img_path):
            lcd.image(5, 2, wifi_img_path)
        else:
            lcd.text(5, 2, "WiFi", lcd.WHITE)

        # --------------------
        # Battery
        # --------------------
        try:
            self.battery_level = machine.battery()  # 0-100
        except:
            self.battery_level = 50
        # Optionally detect charging
        try:
            self.charging = machine.is_charging()
        except:
            self.charging = False

        if self.battery_level < 10:
            # Critical animation
            bat_img_path = self.bat_crit_images[self.bat_crit_index % len(self.bat_crit_images)]
            self.bat_crit_index += 1
        elif self.charging:
            bat_img_path = self.battery_charge_image
        else:
            # Map battery % to battery1-4
            if self.battery_level < 25:
                bat_img_path = self.battery_images[0]
            elif self.battery_level < 50:
                bat_img_path = self.battery_images[1]
            elif self.battery_level < 75:
                bat_img_path = self.battery_images[2]
            else:
                bat_img_path = self.battery_images[3]

        if bat_img_path and os.path.exists(bat_img_path):
            lcd.image(SCREEN_WIDTH-30, 2, bat_img_path)
        else:
            lcd.text(SCREEN_WIDTH-50, 2, "Bat:{}%".format(self.battery_level), lcd.WHITE)

        # --------------------
        # Clock
        # --------------------
        try:
            t = RTC().datetime()
            time_str = "{:02d}:{:02d}:{:02d}".format(t[4], t[5], t[6])
        except:
            time_str = "00:00:00"
        lcd.text(SCREEN_WIDTH//2 - 30, 2, time_str, lcd.WHITE)

# ------------------------------
# POWER "P" SPLASH HANDLER WITH TRUE FADE SIMULATION
# ------------------------------
def handle_power_splash():
    offsplash = os.path.join(ASSETS_PATH, "offsplash.png")
    shutdown_sound = os.path.join(ASSETS_PATH, "shutdown.wav")

    # --- Step 1: fade out menu to black ---
    try:
        import machine
    except:
        pass

    for level in range(10, -1, -1):  # brightness 10->0
        try:
            machine.screen_brightness(level)
        except:
            pass
        time.sleep(0.02)  # 0.22 seconds total

    # --- Step 2: show splash image while black ---
    lcd.clear()
    if os.path.exists(offsplash):
        lcd.image(0, 0, offsplash)

    # --- Step 3: fade in splash ---
    try:
        # Play sound during fade-in
        from m5stack import speaker
        speaker.setVolume(100)
        speaker.playWAV(shutdown_sound)
    except:
        pass

    for level in range(0, 11):  # brightness 0->10
        try:
            machine.screen_brightness(level)
        except:
            pass
        time.sleep(0.03)  # ~0.33 seconds fade-in

    # --- Done, splash fully visible ---

# ------------------------------
# HORIZONTAL MENU
# ------------------------------
class AppMenu:
    def __init__(self):
        self.selected_index = 0
        self.scroll_offset = 0
        self.target_offset = 0
        self.last_aa_presses = []
        if not os.path.exists(APPS_PATH):
            os.mkdir(APPS_PATH)
        self.app_files = [f for f in os.listdir(APPS_PATH) if f.endswith(".py")]
        self.opened_apps = load_json_file(OPENED_APPS_FILE)
        self.status = StatusBar()
        self.load_icons()
        self.draw_menu()

    def load_icons(self):
        self.icons = []
        for app in self.app_files:
            base_name = app[:-3]
            icon_file = os.path.join(ASSETS_PATH, NEW_ICON_NAME) if base_name not in self.opened_apps else os.path.join(ASSETS_PATH, f"{base_name}.png")
            if os.path.exists(icon_file):
                self.icons.append(icon_file)
            else:
                self.icons.append(None)

    def draw_menu(self):
        lcd.clear()
        # Background
        if os.path.exists(BACKGROUND_IMG):
            try:
                lcd.image(0, 0, BACKGROUND_IMG)
            except:
                lcd.clear()
        # Status bar
        self.status.draw()

        # Icons
        y = STATUS_BAR_HEIGHT + (SCREEN_HEIGHT - STATUS_BAR_HEIGHT - ICON_SIZE)//2 - 5
        ICON_TOTAL = ICON_SIZE + ICON_PADDING
        positions = []
        current_x = 0
        for i in range(len(self.icons)):
            if i < self.selected_index:
                positions.append(current_x)
                current_x += ICON_TOTAL
            elif i == self.selected_index:
                positions.append(current_x)
                current_x += ICON_TOTAL + TEXT_WIDTH
            else:
                positions.append(current_x)
                current_x += ICON_TOTAL
        # Smooth scroll
        self.target_offset = positions[self.selected_index] - HIGHLIGHT_X
        self.scroll_offset += (self.target_offset - self.scroll_offset)/ANIMATION_STEPS

        # --- Play hover sound ---
        try:
            from m5stack import speaker
            current_app_name = self.app_files[self.selected_index][:-3]
            sound_file = os.path.join(ASSETS_PATH, f"{current_app_name}.wav")
            if os.path.exists(sound_file):
                speaker.setVolume(100)
                speaker.playWAV(sound_file)
        except:
            pass  # silently ignore if speaker not available or file missing

        for i, icon_path in enumerate(self.icons):
            x = positions[i] - self.scroll_offset
            if x + ICON_SIZE < 0 or x > SCREEN_WIDTH:
                continue

            # Highlighted icon
            if i == self.selected_index:
                lcd.rect(x-2, y-2, ICON_SIZE + TEXT_WIDTH, ICON_SIZE + 4, lcd.YELLOW)
                name = self.app_files[i][:-3]
                lines = textwrap.wrap(name, width=10)[:TEXT_MAX_LINES]
                for idx, line in enumerate(lines):
                    lcd.text(x + ICON_SIZE + 2, y + idx*12, line, lcd.WHITE)

            # Draw icon
            if icon_path and os.path.exists(icon_path):
                lcd.image(x, y, icon_path)
            else:
                lcd.rect(x, y, ICON_SIZE, ICON_SIZE, lcd.WHITE)

    def move_left(self):
        self.selected_index = max(0, self.selected_index-1)
        self.draw_menu()

    def move_right(self):
        self.selected_index = min(len(self.app_files)-1, self.selected_index+1)
        self.draw_menu()

    def launch_app(self):
        if not self.app_files:
            return
        path = os.path.join(APPS_PATH, self.app_files[self.selected_index])
        run_python_app(path)
        name = self.app_files[self.selected_index][:-3]
        if name not in self.opened_apps:
            self.opened_apps.append(name)
            save_json_file(OPENED_APPS_FILE, self.opened_apps)
            self.load_icons()
            self.draw_menu()

    def handle_triple_a(self):
        self.last_aa_presses.append(time.ticks_ms())
        self.last_aa_presses = self.last_aa_presses[-3:]
        if len(self.last_aa_presses) == 3 and (self.last_aa_presses[-1] - self.last_aa_presses[0]) < 2000:
            save_json_file(LOCKED_FILE, {"locked": True})
            machine.reset()

# ------------------------------
# ENTRY LOOP
# ------------------------------
menu = AppMenu()

while True:
    # --- Keyboard P key handler ---
    try:
        import m5stack
        kb = m5stack.machine.Keyboard()
        key = kb.get_key()
        if key == "p":
            handle_power_splash()
    except:
        pass

    # --- Button A (left) ---
    if btnA.isPressed():
        menu.move_left()
        menu.handle_triple_a()
        time.sleep(0.2)

    # --- Button B (enter/open) ---
    if btnB.isPressed():
        menu.launch_app()
        time.sleep(0.2)

    # --- Button C (right) ---
    if btnC.isPressed():
        menu.move_right()
        time.sleep(0.2)

    # --- Status bar redraw ---
    menu.status.draw()
    time.sleep(0.05)
