import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn


# =========================
# CONFIG
# =========================
DEFAULT_MESSAGES = [
"""Hey 👋
I have interacted with your profile & content via @influensor.in by @blackaquaindia.in.
We help creators grow with real engagement 🚀
We can boost your reach using real devices. Interested?",
Want to scale it with real engagement? Let’s connect 💬"""
]


# =========================
# SELECTORS
# =========================
MESSAGE_BTN_SELECTORS = [
    {"text": "Message"},
    {"description": "Message"},
]

INPUT_SELECTORS = [
    {"resourceId": "com.instagram.android:id/row_thread_composer_edittext"},
]

SEND_BTN_SELECTORS = [
    {"description": "Send"},
    {"text": "Send"},
]

# 🔥 Detect existing messages
EXISTING_MESSAGE_SELECTORS = [
    {"resourceId": "com.instagram.android:id/row_message_text"},
    {"textContains": "Seen"},
    {"textContains": "Delivered"},
    {"textContains": "Hey"},
    {"textContains": "@influensor.in"},
    {"textContains": "@blackaquaindia.in"},
]


# =========================
# HELPERS
# =========================
def _find_ui(d, selectors, timeout=3):
    for sel in selectors:
        obj = d(**sel)
        if obj.exists(timeout=timeout):
            return obj
    return None


def has_existing_messages(d):
    for sel in EXISTING_MESSAGE_SELECTORS:
        obj = d(**sel)
        if obj.exists(timeout=2):
            return True
    return False


# =========================
# MAIN FUNCTION
# =========================
def send_promotional_message(device_id, message=None):
    """
    Sends DM ONLY if no previous messages exist.

    Returns:
        True → message sent
        False → skipped / failed
    """

    d = get_device(device_id)

    try:
        # -------------------------
        # 1️⃣ Click Message button
        # -------------------------
        msg_btn = _find_ui(d, MESSAGE_BTN_SELECTORS)

        if msg_btn:
            msg_btn.click()
            time.sleep(2)

        else:
            # 🔥 Already in chat case
            input_box = _find_ui(d, INPUT_SELECTORS)

            if input_box:
                warn("⚠ Already inside chat", device_id)
            else:
                warn("Message button not found", device_id)
                return False

        # -------------------------
        # 2️⃣ Check existing chat
        # -------------------------
        if has_existing_messages(d):
            warn("⚠ Chat already exists → skipping message", device_id)
            d.press("back")
            return False

        # -------------------------
        # 3️⃣ Find input box
        # -------------------------
        input_box = _find_ui(d, INPUT_SELECTORS, timeout=5)

        if not input_box:
            warn("Message input not found", device_id)
            d.press("back")
            return False

        # -------------------------
        # 4️⃣ Prepare message
        # -------------------------
        if not message:
            message = random.choice(DEFAULT_MESSAGES)

        info(f"📩 Sending message: {message}", device_id)

        input_box.click()
        time.sleep(0.5)

        d.clear_text()
        d.send_keys(message, clear=False)
        time.sleep(1)

        # -------------------------
        # 5️⃣ Click Send
        # -------------------------
        send_btn = _find_ui(d, SEND_BTN_SELECTORS)

        if send_btn:
            send_btn.click()
        else:
            d.press("enter")

        time.sleep(2)

        info("✅ Message sent", device_id)

        # -------------------------
        # 6️⃣ Exit chat
        # -------------------------
        d.press("back")
        time.sleep(1)

        return True

    except Exception as e:
        warn(f"Message error: {e}", device_id)

        try:
            d.press("back")
        except:
            pass

        return False