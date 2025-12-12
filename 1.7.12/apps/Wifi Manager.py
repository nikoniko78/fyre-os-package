import os
import time
import json
from M5 import *
from M5Stack import Speaker
import network

# -------------------------------------------------------
# Paths and constants
# -------------------------------------------------------
WIFI_FILE = "/sd/wifi_networks.json"
MAX_NETWORKS = 10

WIFI_PINGING = "/sd/wifipinging.wav"
WIFI_CONNECT = "/sd/wificonnect.wav"
ERROR_SOUND = "/sd/error.wav"

ASSETS_DIR = "/sd/assets"

# Animation frames (PNG files)
CONNECT_ANIM = ["connecting1.png", "connecting2.png", "connecting3.png", "connecting2.png"]

SYSTEM_PASSWORD = "jal190413"

# -------------------------------------------------------
# Load/save networks
# -------------------------------------------------------
def load_networks():
    if os.path.exists(WIFI_FILE):
        with open(WIFI_FILE, "r") as f:
            return json.load(f)
    return []

def save_networks(networks):
    with open(WIFI_FILE, "w") as f:
        json.dump(networks[:MAX_NETWORKS], f)

# -------------------------------------------------------
# Display Wi-Fi icon
# -------------------------------------------------------
def draw_wifi_icon(icon_file):
    screen = M5Screen()
    path = os.path.join(ASSETS_DIR, icon_file)
    if os.path.exists(path):
        try:
            screen.drawImage(path, 0, 0)
        except:
            pass

# -------------------------------------------------------
# Connect to network
# -------------------------------------------------------
def connect_to_network(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Play connecting sound
    if os.path.exists(WIFI_PINGING):
        Speaker.playWAV(WIFI_PINGING, loop=True)

    screen = M5Screen()
    start_time = time.time()
    anim_index = 0

    while not wlan.isconnected() and time.time() - start_time < 15:
        # Animate top-left icon
        draw_wifi_icon(CONNECT_ANIM[anim_index])
        anim_index = (anim_index + 1) % len(CONNECT_ANIM)
        wlan.connect(ssid, password)
        time.sleep(0.5)

    Speaker.stop()

    if wlan.isconnected():
        if os.path.exists(WIFI_CONNECT):
            Speaker.playWAV(WIFI_CONNECT)
        # Determine signal level
        rssi = wlan.status()  # approximate signal strength
        if rssi < 0:  # negative RSSI in UIFlow
            level = min(max(int(-rssi/20),1),4)
        else:
            level = 4
        draw_wifi_icon(f"wifi{level}.png")
        return True
    else:
        if os.path.exists(ERROR_SOUND):
            Speaker.playWAV(ERROR_SOUND)
        draw_wifi_icon("wifi0.png")
        screen.setCursor(10, 30)
        screen.print("Connection failed")
        return False

# -------------------------------------------------------
# Add new network interactively
# -------------------------------------------------------
def add_network():
    screen = M5Screen()
    screen.clean()
    screen.setCursor(10, 10)
    screen.print("Enter SSID:")
    ssid = ""
    while True:
        key = M5Keyboard.getKey()
        if key == "\n":
            break
        elif key:
            ssid += key
            screen.print(key)
        time.sleep(0.05)

    screen.setCursor(10, 30)
    screen.print("Enter Password:")
    password = ""
    while True:
        key = M5Keyboard.getKey()
        if key == "\n":
            break
        elif key:
            password += key
            screen.print("*")
        time.sleep(0.05)

    networks = load_networks()
    networks.insert(0, {"ssid": ssid, "password": password})
    save_networks(networks)
    screen.clean()
    screen.setCursor(10, 10)
    screen.print(f"Saved {ssid}")
    time.sleep(1)

# -------------------------------------------------------
# Main App Loop
# -------------------------------------------------------
def main():
    networks = load_networks()
    screen = M5Screen()
    screen.clean()
    draw_wifi_icon("wifi0.png")

    # Auto-connect saved networks
    for net in networks:
        if connect_to_network(net["ssid"], net["password"]):
            break

    menu = ["Connect to new Wi-Fi", "Exit"]
    selected = 0

    while True:
        # Draw menu
        screen.clean()
        draw_wifi_icon("wifi0.png")
        for i, item in enumerate(menu):
            screen.setCursor(10, 50 + i*20)
            prefix = ">" if i == selected else " "
            screen.print(f"{prefix} {item}")

        key = M5Keyboard.getKey()
        if key == "UP":
            selected = (selected - 1) % len(menu)
        elif key == "DOWN":
            selected = (selected + 1) % len(menu)
        elif key == "\n":
            if selected == 0:
                add_network()
            elif selected == 1:
                break

        # Update live Wi-Fi icon
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            draw_wifi_icon(f"wifi{min(int(wlan.status()/25),4)}.png")
        else:
            draw_wifi_icon("wifi0.png")

        time.sleep(0.1)

if __name__ == "__main__":
    main()
