import time
import random
from engine.ui.device import get_device
from engine.logger import info, warn, error
from engine.ui.swipe import swipe_down


# =========================
# SELECTOR CANDIDATES
# =========================
COMMENT_BUTTON_SELECTORS = [
    {"descriptionContains": "Comment"},
    {"text": "Comment"},
    {"resourceId": "com.instagram.android:id/row_feed_button_comment"},
]

COMMENT_INPUT_SELECTORS = [
    # 🔥 2026 Instagram ID
    {"resourceId": "com.instagram.android:id/layout_comment_thread_edittext_multiline"},

    # Older versions
    {"resourceId": "com.instagram.android:id/comment_edit_text"},
    {"resourceId": "com.instagram.android:id/layout_comment_thread_edittext"},
    {"resourceId": "com.instagram.android:id/row_comment_textview"},

    # Generic fallback
    {"className": "android.widget.EditText"},
    {"className": "android.widget.AutoCompleteTextView"},

    # Hint fallback
    {"textContains": "Add a comment"},
    {"textContains": "Join the conversation"},
    {"textContains": "What do you think of this?"},
]

SEND_BUTTON_SELECTORS = [
    # 🔥 2026 Instagram (your confirmed selector)
    {"resourceId": "com.instagram.android:id/layout_comment_thread_post_button_icon"},

    # Fallbacks
    {"descriptionContains": "Post"},
    {"descriptionContains": "Send"},
    {"text": "Post"},
    {"text": "Send"},
]


# =========================
# HELPER
# =========================
def _find_ui(d, selectors, timeout=2):
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
                swipe_down(device_id)
                time.sleep(1)
                continue

            # -------------------------
            # 3️⃣ Focus input
            # -------------------------
            try:
                input_box.click()
            except Exception:
                warn("⚠ Failed to focus input", device_id)
                swipe_down(device_id)
                continue

            time.sleep(random.uniform(0.5, 1.5))

            if not input_box.exists:
                warn("⚠ Input lost after focus", device_id)
                swipe_down(device_id)
                continue

            # -------------------------
            # 4️⃣ Type comment
            # -------------------------
            try:
                d.clear_text()
            except Exception:
                pass

            try:
                d.send_keys(text, clear=False)
                time.sleep(0.5)  # 🔥 CRITICAL FIX (wait for button activation)
            except Exception as e:
                warn(f"⚠ send_keys failed: {e}", device_id)
                swipe_down(device_id)
                continue

            # Optional verification
            try:
                current_text = input_box.get_text()
                if not current_text or text[:5] not in current_text:
                    warn("⚠ Text not properly entered", device_id)
            except Exception:
                pass
            
            
            # -------------------------
            # 5️⃣ Send comment (FIXED)
            # -------------------------
            send_btn = None

            for _ in range(3):  # retry loop
                send_btn = _find_ui(d, SEND_BUTTON_SELECTORS, timeout=2)

                if send_btn:
                    break
            
            if send_btn:
                try:
                    send_btn.click()
                    time.sleep(random.uniform(0.5, 1.5))
                    info("✅ Comment Posted", device_id)
                    # -------------------------
                    # 6️⃣ Close comment sheet
                    # -------------------------
                    try:
                        swipe_down(device_id)
                    except Exception:
                        pass

                    time.sleep(random.uniform(0.5, 1.5))
                    return True

                except Exception as e:
                    warn(f"⚠ Send click failed: {e}", device_id)

            # -------------------------
            # 🔥 FALLBACK (ICON CLICK)
            # -------------------------
            warn("⚠ Send button not found → fallback tap", device_id)

            w, h = d.window_size()
            d.click(int(w * 0.92), int(h * 0.92))
            time.sleep(0.5)

            info("✅ Comment Posted (fallback)", device_id)

            try:
                swipe_down(device_id)
            except Exception:
                pass

            return True

        except Exception as e:
            error(f"❌ Comment attempt crashed: {e}", device_id)

            try:
                swipe_down(device_id)
            except Exception:
                pass

            time.sleep(1)

    error("❌ Comment failed after retries", device_id)
    return False