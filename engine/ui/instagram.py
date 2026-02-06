import time
import subprocess
import uiautomator2 as u2
from engine.ui.device import get_device

from engine.logger import info, warn, error


INSTAGRAM_PKG = "com.instagram.android"
INSTAGRAM_HOME_TAB = "com.instagram.android:id/tab_avatar"
PROFILE_USERNAME_ID = "com.instagram.android:id/profile_header_banner_item_title"
REEL_AUTHOR_ID = "com.instagram.android:id/clips_author_username"

# ==================================================
# OPEN INSTAGRAM (WITH RETRY)
# ==================================================
def open_instagram(device_id, retries=5):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"Opening Instagram (attempt {attempt})", device_id)
        try:
            d.app_stop(INSTAGRAM_PKG)
            time.sleep(1)
            d.app_start(INSTAGRAM_PKG)
            time.sleep(5)

            if d(resourceId=INSTAGRAM_HOME_TAB).exists(timeout=3):
                return True
        except Exception:
            pass

        time.sleep(1)

    error("Failed to open Instagram", device_id)
    return False


# ==================================================
# UI HELPER: OPEN PROFILE BY USERNAME
# (BEST-EFFORT, NO HARD VERIFY)
# ==================================================
def ui_open_profile_by_username(device_id, username, retries=1):
    d = get_device(device_id)
    url = f"https://www.instagram.com/{username}/"

    for attempt in range(1, retries + 1):
        info(f"Opening profile @{username} (attempt {attempt})", device_id)

        subprocess.run([
            "adb", "-s", device_id,
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", url,
            "-p", INSTAGRAM_PKG
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        time.sleep(3)

        # Verify correct profile opened
        if d(resourceId=PROFILE_USERNAME_ID).exists(timeout=3):
            ui_username = d(resourceId=PROFILE_USERNAME_ID).get_text().strip().lower()
            if ui_username == username.lower():
                return True
            else:
                warn(f"Wrong profile loaded: {ui_username}", device_id)

        time.sleep(1)

    error(f"Failed to open profile @{username}", device_id)
    return False


# ==================================================
# UI HELPER: OPEN POST / REEL
# ==================================================
def open_post_by_url(device_id, post_url, username, retries=3):
    d = get_device(device_id)
    target = username.lower() if username else None

    for attempt in range(1, retries + 1):
        info(f"Opening post (attempt {attempt})", device_id)

        subprocess.run(
            ["adb", "-s", device_id, "shell", "am", "start",
             "-a", "android.intent.action.VIEW", "-d", post_url, "-p", INSTAGRAM_PKG],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        time.sleep(1)
        if not target:
            return True

        if d(resourceId=REEL_AUTHOR_ID).exists(timeout=3):
            author = d(resourceId=REEL_AUTHOR_ID).get_text().strip().lower()
            collab = [u.strip() for u in author.replace("and", ",").split(",") if u.strip()]

            if target in author or target in collab:
                return True

            warn(f"Wrong profile loaded: {collab}", device_id)

        time.sleep(1)

    error("Failed to open post", device_id)
    return False
