import time
from engine.ui.device import get_device


def share_to_story(device_id):
    d = get_device(device_id)
    # -------------------------
    # Helpers
    # -------------------------
    w, h = d.window_size()
    center_x = int(w * 0.5)      # 50%
    center_y = int(h * 0.45)     # 45%

    def drag_down(offset):
        # long press + drag
        d.swipe(
            center_x,
            center_y,
            center_x,
            center_y + offset,
            duration=0.3
        )
        time.sleep(0.8)

    # 1️⃣ Share
    share_btn = d(descriptionContains="Share")
    if not share_btn.exists(timeout=5):
        print(f"[{device_id}] Share button not found")
        return False

    share_btn.click()
    time.sleep(2)

    # 2️⃣ Add to story
    add_story = d(textContains="Add to story")
    if not add_story.exists(timeout=5):
        print(f"[{device_id}] Add to story not found")
        d.press("back")
        return False

    add_story.click()
    time.sleep(10)
    
    def tap_text_button():
        d.click(550, 200)
        time.sleep(1)

    # ---------- LINE 1 ----------
    tap_text_button()
    d.send_keys("Engagement Delivered", clear=False)
    time.sleep(1)

    # ---------- LINE 2 ----------
    tap_text_button()
    d.send_keys("@influensor.in", clear=False)
    time.sleep(1)

    mention = d(textContains="influensor.in")
    if mention.exists(timeout=2):
        mention.click()
        time.sleep(0.5)
    drag_down(180)
    time.sleep(0.5)

    # ---------- LINE 3 ----------
    tap_text_button()
    d.send_keys("@blackaquaindia.in", clear=False)
    time.sleep(1)

    mention = d(textContains="blackaquaindia.in")
    if mention.exists(timeout=2):
        mention.click()
        time.sleep(0.5)
    drag_down(190)
    time.sleep(0.5)
    
    # 4️⃣ Share → Your story
    your_story = d(textContains="Your story")
    if not your_story.exists(timeout=10):
        print(f"[{device_id}] Your story button not found")
        d.press("back")
        d.press("back")
        return False

    your_story.click()
    time.sleep(3)

    d.press("back")
    print(f"[{device_id}] Shared to story with 3 text layers")
    return True
