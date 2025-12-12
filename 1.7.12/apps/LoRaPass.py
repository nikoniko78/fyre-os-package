# LoRaPass - UIFlow2 app for Cardputer ADV + StampS3A
# Features:
# - Background LoRa TX/RX
# - Profile editor (name, country, favorite place, future OS)
# - Custom message box
# - History of passes with RSSI + time
# - Full country list (built-in)
# - Country collection + persistence on /sd/lorapass/
# - StampS3A RGB flashes blue when you collect >0 new countries

from m5stack import *
from m5stack_ui import *
from uiflow import *
import time, os, ubinascii, json, math
import _thread
from machine import Timer, Pin
import ubinascii
try:
    import neopixel
except:
    neopixel = None

# Try to import LoRa interface used in UIFlow environment
# If your firmware exposes a 'lora' module, it should work; otherwise adjust.
try:
    from lora import LoRa
except Exception as e:
    LoRa = None
    print("Warning: LoRa module not found:", e)

# ----------------------------
# CONFIG
# ----------------------------
APP_DIR = "/sd/lorapass"
PROFILE_FILE = APP_DIR + "/profile.json"
HISTORY_FILE = APP_DIR + "/history.json"
COLLECT_FILE = APP_DIR + "/collected.json"
COUNTRIES_FILE = APP_DIR + "/countries.json"

APP_NAME = "LoRaPass"
TX_INTERVAL = 5         # seconds between beacon broadcasts
RX_POLL_MS = 200        # how often receiver thread checks LoRa
FREQUENCY = 868000000   # 868 MHz
SPREADING = 7
BW = 125000

# RSSI thresholds
RSSI_CLOSE = -65
RSSI_MED = -80
RSSI_FAR = -95

# StampS3A NeoPixel pin (1 LED)
NEOPIXEL_PIN = 21
NEO_COUNT = 1

# ----------------------------
# Built-in country list (195+ names)
# (This is a full list to be used for collection)
# ----------------------------
COUNTRIES = [
"Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Aruba","Australia",
"Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin",
"Bhutan","Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Côte d'Ivoire",
"Cabo Verde","Cambodia","Cameroon","Canada","Central African Republic","Chad","Chile","China","Colombia","Comoros",
"Congo (Congo-Brazzaville)","Costa Rica","Croatia","Cuba","Curaçao","Cyprus","Czechia","Democratic Republic of the Congo",
"Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia",
"Eswatini","Ethiopia","Federated States of Micronesia","Fiji","Finland","France","Gabon","Gambia","Georgia","Germany",
"Ghana","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti","Honduras","Hungary",
"Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy","Jamaica","Japan",
"Jordan","Kazakhstan","Kenya","Kiribati","Kosovo","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon",
"Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Maldives",
"Mali","Malta","Marshall Islands","Mauritania","Mauritius","Mexico","Moldova","Monaco","Mongolia","Montenegro",
"Morocco","Mozambique","Myanmar","Namibia","Nauru","Nepal","Netherlands","New Zealand","Nicaragua","Niger",
"Nigeria","North Korea","North Macedonia","Norway","Oman","Pakistan","Palau","Panama","Papua New Guinea","Paraguay",
"Peru","Philippines","Poland","Portugal","Qatar","Romania","Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia",
"Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore",
"Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Korea","South Sudan","Spain","Sri Lanka","Sudan",
"Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania","Thailand","Timor-Leste","Togo",
"Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu","Uganda","Ukraine","United Arab Emirates","United Kingdom",
"United States of America","Uruguay","Uzbekistan","Vanuatu","Vatican City","Venezuela","Vietnam","Yemen","Zambia","Zimbabwe"
]

# ----------------------------
# Helpers: filesystem, JSON persistence
# ----------------------------
def ensure_app_dir():
    try:
        if not os.path.exists(APP_DIR):
            os.makedirs(APP_DIR)
    except Exception as e:
        print("mkdir failed:", e)

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("save failed:", e)

# ----------------------------
# Persistence init
# ----------------------------
ensure_app_dir()
profile = load_json(PROFILE_FILE, {
    "name": "Anon",
    "country": "United States of America",
    "favorite": "Unknown Place",
    "future_os": "LoRaOS",
    "message": "Hello from LoRaPass!"
})
history = load_json(HISTORY_FILE, [])
collected = load_json(COLLECT_FILE, [])

# Ensure countries file exists to let user view full list
if not os.path.exists(COUNTRIES_FILE):
    save_json(COUNTRIES_FILE, COUNTRIES)

# ----------------------------
# NeoPixel (StampS3A) control
# ----------------------------
neo = None
def init_neopixel():
    global neo
    if neopixel:
        try:
            p = Pin(NEOPIXEL_PIN, Pin.OUT)
            neo = neopixel.NeoPixel(p, NEO_COUNT)
            # default off
            neo[0] = (0,0,0)
            neo.write()
        except Exception as e:
            print("Neo init failed:", e)
            neo = None

def neo_set_rgb(r,g,b):
    if neo:
        try:
            neo[0] = (r,g,b)
            neo.write()
        except:
            pass

def flash_blue(times=3, on_ms=150, off_ms=100):
    if not neo: return
    for i in range(times):
        neo_set_rgb(0,0,60)  # blue (tweak brightness if needed)
        time.sleep_ms(on_ms)
        neo_set_rgb(0,0,0)
        time.sleep_ms(off_ms)

init_neopixel()

# ----------------------------
# LoRa init
# ----------------------------
lora_dev = None
device_id = ubinascii.hexlify(machine.unique_id()).decode()

def init_lora():
    global lora_dev
    if LoRa is None:
        print("LoRa module not available on this firmware.")
        return False
    try:
        lora_dev = LoRa(mode=LoRa.LORA_MODE, frequency=FREQUENCY)
        lora_dev.set_spreading_factor(SPREADING)
        lora_dev.set_bandwidth(BW)
        # make sure it's in RX mode
        lora_dev.set_rx()
        return True
    except Exception as e:
        print("LoRa init failed:", e)
        lora_dev = None
        return False

lora_ok = init_lora()

# ----------------------------
# UI - Main Screen
# ----------------------------
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x111111)

title = M5Label(APP_NAME, x=10, y=4, color=0xFFFFFF, font=FONT_MONT_20)
lbl_status = M5Label("Status: starting...", x=10, y=30, color=0x66ccff, font=FONT_MONT_14)
lbl_collected = M5Label("Collected: 0", x=10, y=52, color=0xFFFFFF, font=FONT_MONT_14)
lbl_last = M5Label("Last: none", x=10, y=74, color=0xFFFFFF, font=FONT_MONT_12)

# Buttons (touch or physical) wired to open screens
btn_profile = M5Btn(x=10, y=100, w=140, h=36, text='Profile', bg=0x222222, fg=0xFFFFFF)
btn_history = M5Btn(x=170, y=100, w=140, h=36, text='History', bg=0x222222, fg=0xFFFFFF)
btn_countries = M5Btn(x=10, y=140, w=140, h=36, text='Countries', bg=0x222222, fg=0xFFFFFF)
btn_reset = M5Btn(x=170, y=140, w=140, h=36, text='Reset Collected', bg=0x882222, fg=0xFFFFFF)

# convenience
def update_main_ui():
    lbl_collected.set_text("Collected: {}".format(len(collected)))
    if history:
        last = history[-1]
        lbl_last.set_text("Last: {} ({})".format(last.get("name","?"), last.get("rssi","?")))
    else:
        lbl_last.set_text("Last: none")

update_main_ui()

# ----------------------------
# Profile editor screen
# ----------------------------
def edit_profile():
    # simple text-entry using uiflow dialogs
    global profile
    name = textBox("Name", profile.get("name",""))
    if name is None: return
    country = choiceBox("Country", load_json(COUNTRIES_FILE, COUNTRIES), selected=profile.get("country"))
    if country is None: return
    favorite = textBox("Favorite place", profile.get("favorite",""))
    if favorite is None: return
    future_os = textBox("Future OS", profile.get("future_os",""))
    if future_os is None: return
    message = textBox("Custom message (short)", profile.get("message",""))
    if message is None: return

    profile["name"] = name
    profile["country"] = country
    profile["favorite"] = favorite
    profile["future_os"] = future_os
    profile["message"] = message
    save_json(PROFILE_FILE, profile)
    toast("Profile saved")
    lbl_status.set_text("Status: Profile updated")

# ----------------------------
# History screen
# ----------------------------
def show_history():
    # build readable lines
    lines = []
    for h in reversed(history[-50:]):  # show last 50
        t = time.localtime(h.get("time",0))
        ts = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0],t[1],t[2],t[3],t[4],t[5])
        lines.append("{} | {} | RSSI {}".format(ts, h.get("name","?"), h.get("rssi","?")))
    textBox("History (most recent first)", "\n".join(lines) if lines else "No history yet")

# ----------------------------
# Countries screen
# ----------------------------
def show_countries():
    # Show list with collected status
    lines = []
    for c in load_json(COUNTRIES_FILE, COUNTRIES):
        mark = "✅" if c in collected else "  "
        lines.append("{} {}".format(mark, c))
    textBox("Countries collected", "\n".join(lines))

# ----------------------------
# Reset collected
# ----------------------------
def reset_collected():
    global collected
    if confirmBox("Reset collected?", "Erase collected countries?"):
        collected = []
        save_json(COLLECT_FILE, collected)
        toast("Collected cleared")
        update_main_ui()

# ----------------------------
# UI button handlers
# ----------------------------
btn_profile.pressed(edit_profile)
btn_history.pressed(show_history)
btn_countries.pressed(show_countries)
btn_reset.pressed(reset_collected)

# ----------------------------
# LoRaPass packet format
# ----------------------------
def make_packet():
    pkt = {
        "type": "lorapass",
        "id": device_id,
        "name": profile.get("name",""),
        "country": profile.get("country",""),
        "favorite": profile.get("favorite",""),
        "future_os": profile.get("future_os",""),
        "message": profile.get("message",""),
        "version": 1
    }
    try:
        return json.dumps(pkt)
    except:
        return "{}"

# ----------------------------
# Broadcast timer (uses Timer)
# ----------------------------
tx_timer = None
def tx_callback(t):
    if lora_dev:
        try:
            data = make_packet()
            lora_dev.send(data)
            # update status briefly
            lbl_status.set_text("Status: Beacon sent")
        except Exception as e:
            print("TX error:", e)
            lbl_status.set_text("Status: TX error")
    else:
        # no LoRa available
        lbl_status.set_text("Status: LoRa not init")

# start TX Timer
def start_tx_timer():
    global tx_timer
    try:
        tx_timer = Timer(1)
        tx_timer.init(period=TX_INTERVAL*1000, mode=Timer.PERIODIC, callback=tx_callback)
    except Exception as e:
        print("Failed to start TX timer:", e)

if lora_ok:
    start_tx_timer()
else:
    lbl_status.set_text("Status: LoRa not ready")

# ----------------------------
# Receiver thread
# ----------------------------
received_lock = False
new_countries_since_last_check = 0

def handle_packet(raw, rssi):
    global history, collected, new_countries_since_last_check
    try:
        pkt = json.loads(raw)
    except:
        return
    if not isinstance(pkt, dict): return
    if pkt.get("type") != "lorapass": return
    if pkt.get("id") == device_id: return  # ignore self

    entry = {
        "id": pkt.get("id"),
        "name": pkt.get("name",""),
        "country": pkt.get("country",""),
        "favorite": pkt.get("favorite",""),
        "future_os": pkt.get("future_os",""),
        "message": pkt.get("message",""),
        "rssi": rssi,
        "time": time.time()
    }

    # Add to history (avoid duplicates in immediate succession)
    if not history or history[-1].get("id") != entry["id"] or (time.time() - history[-1].get("time",0))>10:
        history.append(entry)
        # trim history
        if len(history) > 1000:
            history = history[-1000:]
        save_json(HISTORY_FILE, history)

    # Country collection
    c = entry.get("country","")
    if c and c not in collected:
        collected.append(c)
        save_json(COLLECT_FILE, collected)
        new_countries_since_last_check += 1
        # Flash LED blue to indicate new collection
        try:
            flash_blue(times=2)
        except:
            pass

    # UI updates
    lbl_status.set_text("StreetPass from {}".format(entry.get("name","?")))
    lbl_collected.set_text("Collected: {}".format(len(collected)))
    lbl_last.set_text("Last: {} ({})".format(entry.get("name","?"), entry.get("rssi","?")))

def rx_loop():
    global lora_dev
    while True:
        try:
            if not lora_dev:
                time.sleep_ms(RX_POLL_MS)
                continue
            raw = lora_dev.recv()  # non-blocking receive in many LoRa libs, may return bytes or str or None
            if raw:
                # If bytes, decode
                try:
                    if isinstance(raw, bytes):
                        s = raw.decode('utf-8', 'ignore')
                    else:
                        s = str(raw)
                except:
                    s = str(raw)
                # try to read rssi if supported
                rssi = None
                try:
                    rssi = lora_dev.get_rssi()
                except:
                    rssi = 0
                handle_packet(s, rssi)
        except Exception as e:
            print("RX loop error:", e)
        time.sleep_ms(RX_POLL_MS)

# start receiver thread if LoRa available
if lora_ok:
    try:
        _thread.start_new_thread(rx_loop, ())
        lbl_status.set_text("Status: Running")
    except Exception as e:
        print("Thread start failed:", e)
        lbl_status.set_text("Status: RX thread failed")
else:
    lbl_status.set_text("Status: LoRa not ready")

# ----------------------------
# Background indicator (LED) check
# If user opens UI and there's new countries, show a badge and flash once.
# ----------------------------
def check_new_indicator():
    global new_countries_since_last_check
    if new_countries_since_last_check > 0:
        # show small toast and flash once
        toast("New country collected: {}".format(new_countries_since_last_check))
        flash_blue(times=2)
        new_countries_since_last_check = 0

# Add a periodic timer to check indicators (UI safe)
indicator_timer = Timer(2)
indicator_timer.init(period=5000, mode=Timer.PERIODIC, callback=lambda t: check_new_indicator())

# ----------------------------
# Main loop (keeps UIFlow app alive)
# ----------------------------
while True:
    # allow screen interaction; background TX/RX continue via Timer and thread
    wait_ms(200)
