import time
import random
from engine.ui.device import get_device
from engine.logger import info, warn, error


# =========================
# CONFIG
# =========================
STORY_VIEW_MIN = 1
STORY_VIEW_MAX = 1
MAX_STORIES = 10
LIKE_PROBABILITY = 0.75


# =========================
# SELECTOR CANDIDATES
# =========================
STORY_AVATAR_SELECTORS = [
    {"resourceId": "com.instagram.android:id/reel_ring"},
    {"descriptionContains": "Story"},
]

STORY_LIKE_SELECTORS = [
    {"resourceId": "com.instagram.android:id/toolbar_like_button"},
    {"descriptionContains": "Like"},
]


def _find_ui(d, selectors, timeout=1):
    for sel in selectors:
        ui = d(**sel)
        if ui.exists(timeout=timeout):
            return ui
    return None


# =========================
# STORY VIEW + LIKE
# =========================
def story_view_like(device_id, retries=1):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Story View Like (attempt {attempt})", device_id)

        try:
            # -------------------------
            # 1️⃣ Open first story
            # -------------------------
            avatar = _find_ui(d, STORY_AVATAR_SELECTORS, timeout=3)

            if not avatar:
                warn("⚠ Story Avatar Not Found", device_id)
                time.sleep(1)
                continue

            avatar.click()
            time.sleep(2)

            stories_viewed = 0
            w, h = d.window_size()

            # -------------------------
            # 2️⃣ View stories loop
            # -------------------------
            while stories_viewed < MAX_STORIES:
                like_btn = _find_ui(d, STORY_LIKE_SELECTORS, timeout=0.5)

                # 🚪 Exit if stories ended
                if not like_btn:
                    break

                view_time = random.randint(STORY_VIEW_MIN, STORY_VIEW_MAX)
                time.sleep(view_time)

                # ❤️ Random like (only if NOT already liked)
                if random.random() < LIKE_PROBABILITY:
                    try:
                        info_obj = like_btn.info
                        desc = (info_obj.get("contentDescription") or "").lower()

                        if "liked" not in desc:
                            like_btn.click()
                            info("❤️ Liked Story", device_id)
                            time.sleep(0.1)
                        else:
                            info("⚠ Story Already Liked → Skipping", device_id)

                    except Exception:
                        # fallback (keep original behavior safe)
                        like_btn.click()
                        info("❤️ Liked Story (fallback)", device_id)
                        time.sleep(0.1)

                # 👉 Next story (tap right side)
                d.click(int(w * 0.99), int(h * 0.25))
                time.sleep(0.1)

                stories_viewed += 1

            info(f"✅ Story View Like Done ({stories_viewed} Stories)", device_id)
            return True

        except Exception as e:
            warn(f"⚠ Story View Like Error: {e}", device_id)
            try:
                d.press("back")
            except Exception:
                pass
            time.sleep(1)

    error("❌ Story View Like Failed After Retries", device_id)
    return False
