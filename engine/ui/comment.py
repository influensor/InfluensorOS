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

        try:
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
            # 3️⃣ Focus input safely
            # -------------------------
            try:
                input_box.click()
            except Exception:
                warn("⚠ Failed to focus input", device_id)
                d.press("back")
                continue

            time.sleep(random.uniform(0.6, 1.2))

            # Confirm still exists
            if not input_box.exists:
                warn("⚠ Input lost after focus", device_id)
                d.press("back")
                continue

            # -------------------------
            # 4️⃣ Type comment safely
            # -------------------------
            try:
                d.clear_text()
            except Exception:
                pass  # Safe ignore

            try:
                d.send_keys(text, clear=False)
                time.sleep(random.uniform(1.0, 1.8))
            except Exception as e:
                warn(f"⚠ send_keys failed: {e}", device_id)
                d.press("back")
                continue

            # Optional verification (very safe)
            try:
                current_text = input_box.get_text()
                if not current_text or text[:5] not in current_text:
                    warn("⚠ Text not properly entered", device_id)
            except Exception:
                pass

            # -------------------------
            # 5️⃣ Send comment
            # -------------------------
            send_btn = _find_ui(d, SEND_BUTTON_SELECTORS)

            if not send_btn:
                warn("⚠ Send button not found", device_id)
                d.press("back")
                continue

            try:
                sent = d.press("enter") or send_btn.click()
            except Exception:
                sent = False

            if sent:
                info("✅ Comment Posted", device_id)
                time.sleep(random.uniform(1.5, 2.5))

                # -------------------------
                # 6️⃣ Close comment sheet
                # -------------------------
                try:
                    d.press("back")
                    d.press("back")
                except Exception:
                    pass

                time.sleep(random.uniform(1.0, 1.8))
                return True

            warn("⚠ Comment send failed", device_id)
            time.sleep(1)

        except Exception as e:
            # 🔒 Ultimate protection — never crash worker
            error(f"❌ Comment attempt crashed: {e}", device_id)

            try:
                d.press("back")
            except Exception:
                pass

            time.sleep(1)

    error("❌ Comment failed after retries", device_id)
    return False
