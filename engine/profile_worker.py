import os
import time
from engine.logger import info, warn, error
from engine.ui.device import get_device
from engine.ui.instagram import (open_instagram,ui_open_profile_by_username,)
from engine.ui.story_view_like import story_view_like

# ==========================================
# CONFIGURATION
# ==========================================

USERNAME_FILE = (
    r"C:\Users\yagha\OneDrive\Documents\GitHub"
    r"\InfluensorOS\data\mentions\usernames.txt"
)

FOUND_FILE = os.path.join(os.path.dirname(USERNAME_FILE),"usernames_found.txt")
USERNAME_COOLDOWN = 1
CYCLE_COOLDOWN = 3


# ==========================================
# PROFILE DETECTION
# ==========================================

NOT_FOUND_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/no_found_text"
    },
    {
        "resourceId":
        "com.instagram.android:id/igds_headline_emphasized_headline"
    },
    {
        "text": "User not found"
    },
]

PROFILE_SELECTOR = {
    "resourceId":
    "com.instagram.android:id/profile_header_container"
}


def check_profile_status(d):
    time.sleep(1)
    # Check if Instagram displays User not found.
    for selector in NOT_FOUND_SELECTORS:
        try:
            if d(**selector).exists(timeout=0.5):
                return "NOT_FOUND"
        except Exception:
            pass

    # Check whether profile screen is available.
    try:
        if d(**PROFILE_SELECTOR).exists(timeout=3):
            # Verify not-found message is absent.
            for selector in NOT_FOUND_SELECTORS:
                if d(**selector).exists(timeout=0.3):
                    return "NOT_FOUND"
            return "FOUND"
    except Exception:
        pass
    return "UNKNOWN"


# ==========================================
# USERNAME FILE
# ==========================================

def load_usernames():
    if not os.path.exists(USERNAME_FILE):
        warn(f"Username file not found: {USERNAME_FILE}")
        return []

    usernames = []

    try:
        with open(USERNAME_FILE,"r",encoding="utf-8-sig") as file:
            for line in file:
                username = line.strip().lstrip("@")
                if (username and not username.startswith("#")):
                    usernames.append(username)

    except Exception as e:
        error(f"Username file read error: {e}")
        return []

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(usernames))


# ==========================================
# SAVE FOUND USERNAMES
# ==========================================

def save_found_username(username):
    os.makedirs(os.path.dirname(FOUND_FILE),exist_ok=True)
    existing = set()

    if os.path.exists(FOUND_FILE):
        with open(FOUND_FILE,"r",encoding="utf-8") as file:
            existing = {line.strip().lower() for line in file if line.strip()}

    if username.lower() not in existing:
        with open(FOUND_FILE,"a",encoding="utf-8") as file:
            file.write(username + "\n")

        info(f"Saved @{username} to usernames_found.txt")


# ==========================================
# PROCESS USERNAME
# ==========================================

def process_username(device_id, d, username):
    info(f"Opening profile @{username}", device_id)
    try:
        # Navigate to Instagram profile.
        ui_open_profile_by_username(device_id,username)
        time.sleep(1)

        # Validate profile.
        status = check_profile_status(d)
        if status == "NOT_FOUND":
            warn(f"User not found: @{username}",device_id)
            return

        if status == "UNKNOWN":
            warn(f"Unable to verify profile: @{username}",device_id)
            return

        # Save confirmed username.
        save_found_username(username)

        info(f"Profile found: @{username}",device_id)

        # Execute existing story module.
        story_view_like(device_id)

    except Exception as e:
        error(f"Error processing @{username}: {e}",device_id)


# ==========================================
# MAIN DEVICE WORKER
# ==========================================

def device_worker(device_id):
    info("Profile Worker Started", device_id)
    try:
        d = get_device(device_id)
        open_instagram(device_id)

    except Exception as e:
        error(f"Instagram startup failed: {e}",device_id)
        return

    # ======================================
    # CONTINUOUS USERNAME CYCLE
    # ======================================

    while True:
        usernames = load_usernames()
        if not usernames:
            warn("No usernames found in input file",device_id)
            time.sleep(CYCLE_COOLDOWN)
            continue

        info(f"Loaded {len(usernames)} usernames",device_id)

        for index, username in enumerate(usernames,start=1):
            info(f"Username {index}/{len(usernames)}: @{username}",device_id)
            process_username(device_id,d,username)
            time.sleep(USERNAME_COOLDOWN)

        info("Username cycle completed. Reloading file...",device_id)
        time.sleep(CYCLE_COOLDOWN)
