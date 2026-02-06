import time
import random
from engine.ui.device import get_device

from engine.logger import info, warn, error


# =========================
# SELECTOR CANDIDATES
# =========================
COMMENT_BUTTON_SELECTORS = [
    {"descriptionContains": "Comment"},
    {"text": "Comment"},
    {"resourceId": "com.instagram.android:id/row_feed_button_comment"},
]

COMMENT_INPUT_SELECTORS = [
    {
        "className": "android.widget.AutoCompleteTextView",
        "resourceId": "com.instagram.android:id/layout_comment_thread_edittext"
    }
]

SEND_BUTTON_SELECTORS = [
    {"descriptionContains": "Post"},
    {"text": "Post"},
]


def _find_ui(d, selectors, timeout=1):
    for sel in selectors:
        ui = d(**sel)
        if ui.exists(timeout=timeout):
            return ui
    return None


# =========================
# COMMENT EXECUTION
# =========================
def post_comment(device_id, text, retries=2):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Comment Post (attempt {attempt})", device_id)

        # -------------------------
        # 1️⃣ Open comments
        # -------------------------
        comment_btn = _find_ui(d, COMMENT_BUTTON_SELECTORS)

        if not comment_btn:
            warn("⚠ Comment button not found", device_id)
            time.sleep(1)
            continue

        comment_btn.click()
        time.sleep(random.uniform(2.0, 3.0))

        # -------------------------
        # 2️⃣ Locate comment input
        # -------------------------
        input_box = _find_ui(d, COMMENT_INPUT_SELECTORS)

        if not input_box:
            warn("⚠ Comment input not found", device_id)
            d.press("back")
            time.sleep(1)
            continue

        # -------------------------
        # 3️⃣ Focus input
        # -------------------------
        input_box.click()
        time.sleep(random.uniform(0.6, 1.2))

        # -------------------------
        # 4️⃣ Type comment
        # -------------------------
        d.clear_text()
        d.send_keys(text, clear=False)
        time.sleep(random.uniform(1.0, 1.8))

        # -------------------------
        # 5️⃣ Send comment
        # -------------------------
        send_btn = _find_ui(d, SEND_BUTTON_SELECTORS)

        if not send_btn:
            warn("⚠ Send button not found", device_id)
            d.press("back")
            time.sleep(1)
            continue

        sent = d.press("enter") or send_btn.click()

        if sent:
            info("✅ Comment Posted", device_id)
            time.sleep(random.uniform(1.5, 2.5))

            # -------------------------
            # 6️⃣ Close comment sheet
            # -------------------------
            d.press("back")
            d.press("back")
            time.sleep(random.uniform(1.0, 1.8))
            return True

        warn("⚠ Comment send failed", device_id)
        time.sleep(1)

    error("❌ Comment failed after retries", device_id)
    return False
