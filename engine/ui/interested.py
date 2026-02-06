import time
import random
from engine.ui.device import get_device

from engine.logger import info, warn, error


# =========================
# SELECTOR CANDIDATES
# =========================
MORE_BUTTON_SELECTORS = [
    {"descriptionContains": "More"},
    {"resourceId": "com.instagram.android:id/row_feed_button_more"},
]

INTERESTED_SELECTORS = [
    {"textMatches": "(?i)interested"},
    {"textContains": "Interested"},
]


def _find_ui(d, selectors, timeout=1):
    for sel in selectors:
        ui = d(**sel)
        if ui.exists(timeout=timeout):
            return ui
    return None


# =========================
# INTERESTED EXECUTION
# =========================
def mark_post_interested(device_id, retries=2):
    """
    Marks the currently opened post/reel as 'Interested'
    Returns True if successful, False otherwise
    """

    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Mark Interested (attempt {attempt})", device_id)

        # -------------------------
        # 1️⃣ Open More (⋮)
        # -------------------------
        more_btn = _find_ui(d, MORE_BUTTON_SELECTORS, timeout=2)

        if not more_btn:
            warn("⚠ More button not found", device_id)
            time.sleep(1)
            continue

        more_btn.click()
        time.sleep(random.uniform(0.8, 1.2))

        # -------------------------
        # 2️⃣ Click Interested
        # -------------------------
        interested = _find_ui(d, INTERESTED_SELECTORS, timeout=3)

        if interested:
            interested.click()
            time.sleep(random.uniform(0.6, 1.0))
            info("✅ Post marked as Interested", device_id)
            return True

        # -------------------------
        # 3️⃣ Cleanup
        # -------------------------
        warn("⚠ Interested option not found", device_id)
        d.press("back")
        time.sleep(1)

    error("❌ Mark Interested failed after retries", device_id)
    return False
