# ------------------------------
# Scan for JSON and TXT files
# ------------------------------
json_files = []
text_files = []

def scan_config_files(path="/sd"):
    global json_files, text_files
    json_files = []
    text_files = []
    for root, dirs, files in os.walk(path):
        # Skip notes folder
        if "/sd/notes" in root:
            continue
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
            elif file.endswith(".txt"):
                text_files.append(os.path.join(root, file))

# Combine all files for the interface
def get_all_files():
    return json_files + text_files

# ------------------------------
# Update display and selection
# ------------------------------
scan_config_files()
all_files = get_all_files()
selected_file_idx = 0
selected_key_idx = 0
current_keys = []
current_values = []
editing_value = False

def refresh_keys_values():
    global current_keys, current_values
    file_path = all_files[selected_file_idx]
    if file_path.endswith(".json"):
        data = load_json(file_path)
        current_keys = list(data.keys())
        current_values = list(data.values())
    else:  # TXT file: treat each line as a key=value
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
            current_keys = []
            current_values = []
            for line in lines:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    current_keys.append(k)
                    current_values.append(v)
        except:
            current_keys = []
            current_values = []

def save_current_file():
    file_path = all_files[selected_file_idx]
    if file_path.endswith(".json"):
        save_json(file_path, dict(zip(current_keys, current_values)))
    else:  # Save TXT file
        try:
            with open(file_path, "w") as f:
                for k, v in zip(current_keys, current_values):
                    f.write(f"{k}={v}\n")
        except:
            pass
