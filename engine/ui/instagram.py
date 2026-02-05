import time
import subprocess
import uiautomator2 as u2
from engine.ui.device import get_device

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
        print(f"[{device_id}] Opening Instagram (attempt {attempt})")

        try:
            d.app_stop(INSTAGRAM_PKG)
            time.sleep(1)
            d.app_start(INSTAGRAM_PKG)
            time.sleep(5)

            # Verify app launched
            if d(resourceId=INSTAGRAM_HOME_TAB).exists(timeout=3):
                return True

        except Exception:
            pass

        time.sleep(1)

    print(f"[{device_id}] Failed to open Instagram")
    return False


# ==================================================
# OPEN PROFILE BY USERNAME (VERIFY USERNAME)
# ==================================================
def open_profile_by_username(device_id, username, retries=5):
    d = get_device(device_id)
    url = f"https://www.instagram.com/{username}/"

    for attempt in range(1, retries + 1):
        print(f"[{device_id}] Opening profile @{username} (attempt {attempt})")

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
                print(
                    f"[{device_id}] Wrong profile loaded: {ui_username}"
                )

        time.sleep(1)

    print(f"[{device_id}] Failed to open profile @{username}")
    return False


# ==================================================
# OPEN POST / REEL (VERIFY AUTHOR)
# ==================================================
# ==================================================
# OPEN POST / REEL (VERIFY AUTHOR)
# ==================================================
def open_post_by_url(device_id, post_url, username, retries=5):
    d = get_device(device_id)
    target = username.lower() if username else None

    for attempt in range(1, retries + 1):
        print(f"[{device_id}] Opening post (attempt {attempt})")

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

            print(f"[{device_id}] Wrong profile loaded: {collab}")

        time.sleep(1)

    print(f"[{device_id}] Failed to open post")
    return False
