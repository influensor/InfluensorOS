import time
import random
import subprocess

from engine.ui.device import get_device
from engine.logger import info, warn, error

# =========================
# CONFIG
# =========================

GIF_KEYWORDS = [
    "love", "wow", "cool", "nice",
    "amazing", "awesome", "fire"
]

SEARCH_GIPHY_CENTER = (612, 243)  # confirmed working
KEYBOARD_TAP = (600, 1200)        # dummy tap to force keyboard

# =========================
# ADB HELPERS
# =========================

def adb(device_id, cmd):
    subprocess.run(
        ["adb", "-s", device_id, "shell"] + cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def adb_tap(device_id, x, y):
    adb(device_id, ["input", "tap", str(x), str(y)])

def adb_swipe(device_id, x1, y1, x2, y2, duration=300):
    adb(device_id, [
        "input", "swipe",
        str(x1), str(y1), str(x2), str(y2), str(duration)
    ])

# =========================
# MAIN FUNCTION
# =========================

def post_gif_comment(device_id, retries=2):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ GIF Comment (attempt {attempt})", device_id)

        try:
            # 1️⃣ Open comment sheet
            d(descriptionContains="Comment").click()
            time.sleep(1.8)

            # 2️⃣ Open GIF picker
            d(resourceId="com.instagram.android:id/comment_composer_animated_image_picker_button").click()
            time.sleep(1.8)

            w, h = d.window_size()

            # 3️⃣ FORCE expand bottom sheet (CRITICAL)
            adb_swipe(
                device_id,
                w // 2, int(h * 0.85),
                w // 2, int(h * 0.30),
                duration=400
            )
            time.sleep(1.2)

            # 4️⃣ Tap Search GIPHY TWICE (focus hack)
            adb_tap(device_id, *SEARCH_GIPHY_CENTER)
            time.sleep(0.4)
            adb_tap(device_id, *SEARCH_GIPHY_CENTER)
            time.sleep(0.6)

            # 5️⃣ Force keyboard
            adb_tap(device_id, *KEYBOARD_TAP)
            time.sleep(0.4)

            # 6️⃣ Type keyword
            keyword = random.choice(GIF_KEYWORDS)
            info(f"GIF keyword → {keyword}", device_id)
            adb(device_id, ["input", "text", keyword])
            time.sleep(2)

            # 7️⃣ Scroll results
            adb_swipe(
                device_id,
                w // 2, int(h * 0.75),
                w // 2, int(h * 0.45),
                duration=250
            )
            time.sleep(1)

            # 8️⃣ Tap random GIF
            x = random.randint(int(w * 0.2), int(w * 0.8))
            y = random.randint(int(h * 0.45), int(h * 0.80))

            adb_tap(device_id, x, y)
            time.sleep(1)

            # 9️⃣ Exit
            d.press("back")
            time.sleep(0.5)
            d.press("back")

            info("✅ GIF comment posted", device_id)
            return True

        except Exception as e:
            warn(f"GIF error: {e}", device_id)
            try:
                d.press("back")
            except Exception:
                pass
            time.sleep(1)

    error("❌ GIF comment failed after retries", device_id)
    return False
