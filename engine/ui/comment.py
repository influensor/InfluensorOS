import time
import random
from engine.ui.device import get_device


def post_comment(device_id, text):
    d = get_device(device_id)

    # -------------------------
    # 1️⃣ Open comments
    # -------------------------
    comment_btn = d(descriptionContains="Comment")
    if not comment_btn.exists:
        comment_btn = d(resourceId="com.instagram.android:id/row_feed_button_comment")

    if not comment_btn.exists:
        print(f"[{device_id}] Comment button not found")
        return False

    comment_btn.click()
    time.sleep(random.uniform(2.0, 3.0))

    # -------------------------
    # 2️⃣ Locate REAL comment input
    # (matches your XML exactly)
    # -------------------------
    input_box = d(
        className="android.widget.AutoCompleteTextView",
        resourceId="com.instagram.android:id/layout_comment_thread_edittext"
    )

    if not input_box.exists:
        print(f"[{device_id}] Comment input not available, skipping")
        d.press("back")
        return False

    # -------------------------
    # 3️⃣ Focus input
    # -------------------------
    input_box.click()
    time.sleep(random.uniform(0.6, 1.2))

    # -------------------------
    # 4️⃣ Type comment using UiAutomator2 IME
    # -------------------------
    d.clear_text()
    d.send_keys(text, clear=False)
    time.sleep(random.uniform(1.0, 1.8))

    # -------------------------
    # 5️⃣ Send comment
    # -------------------------
    send_btn = d(descriptionContains="Post")
    if not send_btn.exists:
        print(f"[{device_id}] Send button not found")
        d.press("back")
        return False
    
    sent = d.press("enter") or send_btn.click()
    if sent:
        time.sleep(random.uniform(1.5, 2.5))
        # -------------------------
        # 6️⃣ Close comment bottom sheet
        # -------------------------
        d.press("back")
        d.press("back")
        time.sleep(random.uniform(1.0, 1.8))
    
    return True
