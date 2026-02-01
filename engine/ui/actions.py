import time
from engine.ui.device import get_device

def like_post(device_id):
    d = get_device(device_id)

    # Strategy:
    # Instagram like button usually has content-desc "Like"
    # We try safe selectors

    like_btn = d(descriptionContains="Like")

    if like_btn.exists:
        like_btn.click()
        time.sleep(1)
        return True

    # fallback: heart icon resource-id
    like_btn = d(resourceId="com.instagram.android:id/row_feed_button_like")
    if like_btn.exists:
        like_btn.click()
        time.sleep(1)
        return True

    print(f"[{device_id}] Like button not found")
    return False
