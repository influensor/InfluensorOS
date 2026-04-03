import time
from engine.ui.device import get_device
from engine.logger import info, warn

MAX_EMPTY_SCROLLS = 10

# =========================
# SELECTORS
# =========================
STORY_BUTTON = {
    "resourceId": "com.instagram.android:id/row_user_imageview",
    "descriptionContains": "story"
}

STORY_LIKE_BTN = {
    "resourceId": "com.instagram.android:id/toolbar_like_button"
}


# =========================
# STORY HANDLER
# =========================

def _like_story_until_end(device_id):
    d = get_device(device_id)
    liked_once = False
    story_like = d(**STORY_LIKE_BTN)
    while True:
        clicked = story_like.click_exists(timeout=0.1)
        if not clicked:
            if liked_once:
                break
            time.sleep(0.1)
            continue
        liked_once = True
        info("❤️ Story liked", device_id)
        w, h = d.window_size()
        d.click(int(w * 0.99), int(h * 0.5))
        time.sleep(0.1)

# =========================
# MAIN ENGINE
# =========================

def story_like_from_likes(device_id):
    d = get_device(device_id)
    info("🔥 STORY LOOP START", device_id)
    empty_scrolls = 0
    while True:
        users = d(**STORY_BUTTON)
        # ✅ reset when users found
        if users.exists:
            empty_scrolls = 0
        # ❗ If no users → scroll & retry
        if not users.exists:
            empty_scrolls += 1
            warn(f"⚠ No story users → scrolling ({empty_scrolls})", device_id)
            if empty_scrolls >= MAX_EMPTY_SCROLLS:
                warn("🚪 Too many empty scrolls → exiting likes screen", device_id)
                try:
                    d.press("back")
                    time.sleep(0.1)  # ✅ REQUIRED
                except Exception:
                    pass
                return False
            w, h = d.window_size()
            d.swipe(int(w * 0.5), int(h * 0.8),
                    int(w * 0.5), int(h * 0.3), 0.1)
            time.sleep(0.1)  # ✅ REQUIRED (load new users)
            continue
        try:
            desc = users[0].info.get("contentDescription", "")
            info(f"▶ Opening → {desc}", device_id)
            users[0].click()
            time.sleep(0.1)  # ✅ REQUIRED (story open)
            _like_story_until_end(device_id)
        except Exception as e:
            warn(f"⚠ Error opening story: {e}", device_id)
            time.sleep(0.1)  # ✅ REQUIRED
