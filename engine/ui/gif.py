import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn, error


# =========================
# CONFIG
# =========================

GIF_KEYWORDS = [
    "love", "wow", "cool", "nice",
    "amazing", "awesome", "fire"
]


# =========================
# MAIN FUNCTION
# =========================

def post_gif_comment(device_id, retries=2):
    """
    Posts a random GIF comment on currently opened Instagram post/reel.

    Requirements:
    - Post must already be open
    - Comment icon must be visible

    Returns True if successful, else False
    """

    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ GIF Comment (attempt {attempt})", device_id)

        try:
            # -------------------------
            # 1️⃣ Open comment sheet
            # -------------------------
            comment_btn = d(descriptionContains="Comment")

            if not comment_btn.exists(timeout=3):
                warn("Comment button not found", device_id)
                return False

            comment_btn.click()
            time.sleep(1.5)

            # -------------------------
            # 2️⃣ Open GIF picker
            # -------------------------
            gif_btn = d(
                resourceId="com.instagram.android:id/comment_composer_animated_image_picker_button"
            )

            if not gif_btn.exists(timeout=3):
                warn("GIF picker button not found", device_id)
                d.press("back")
                return False

            gif_btn.click()
            time.sleep(1.5)

            # -------------------------
            # 3️⃣ Wait for Search GIPHY box
            # -------------------------
            search_box = d(
                resourceId="com.instagram.android:id/search_edit_text"
            )

            if not search_box.exists(timeout=5):
                warn("Search GIPHY box not found", device_id)
                d.press("back")
                d.press("back")
                return False

            search_box.click()
            time.sleep(0.5)

            # -------------------------
            # 4️⃣ Type random keyword
            # -------------------------
            keyword = random.choice(GIF_KEYWORDS)
            info(f"GIF keyword → {keyword}", device_id)

            d.clear_text()
            d.send_keys(keyword, clear=False)
            time.sleep(2)

            # -------------------------
            # 5️⃣ Wait for GIF results
            # -------------------------
            gif_buttons = d(
                className="android.widget.Button",
                resourceId="com.instagram.android:id/gif_image"
            )

            if not gif_buttons.exists(timeout=5):
                warn("GIF results not loaded", device_id)
                d.press("back")
                d.press("back")
                return False

            count = gif_buttons.count

            if count == 0:
                warn("GIF list empty", device_id)
                d.press("back")
                d.press("back")
                return False

            # -------------------------
            # Optional human-like scroll
            # -------------------------
            grid = d(resourceId="com.instagram.android:id/gifs_tray_grid")

            if grid.exists and random.random() < 0.4:
                grid.scroll.vert.forward(steps=10)
                time.sleep(1)
                count = gif_buttons.count

            if count == 0:
                warn("No GIFs after scroll", device_id)
                return False

            # -------------------------
            # 6️⃣ Click random GIF
            # -------------------------
            index = random.randint(0, count - 1)
            gif_buttons[index].click()
            time.sleep(1)

            # -------------------------
            # 7️⃣ Close comment sheet
            # -------------------------
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