import time
from engine.ui.device import get_device


def retry_step(step_name, retries, delay, fn):
    for attempt in range(1, retries + 1):
        try:
            if fn():
                return True
            raise Exception(f"{step_name} condition failed")
        except Exception as e:
            print(f"{step_name} failed ({attempt}/{retries}) → {e}")
            if attempt < retries:
                time.sleep(delay)
    return False


def add_to_story(device_id):
    d = get_device(device_id)

    # 1️⃣ Share
    if not retry_step(
        "Share button",
        retries=5,
        delay=2,
        fn=lambda: (
            d(descriptionContains="Share").exists(timeout=5)
            and d(descriptionContains="Share").click() is None
        )
    ):
        return False

    time.sleep(1)

    # 2️⃣ Add to story
    if not retry_step(
        "Add to story",
        retries=5,
        delay=2,
        fn=lambda: (
            d(textContains="Add to story").exists(timeout=5)
            and d(textContains="Add to story").click() is None
        )
    ):
        d.press("back")
        return False

    time.sleep(10)

    # 3️⃣ Add a caption
    if not retry_step(
        "Add a caption",
        retries=10,
        delay=2,
        fn=lambda: (
            d(textContains="Add a caption").exists(timeout=5)
            and d(textContains="Add a caption").click() is None
        )
    ):
        return False

    time.sleep(1)

    # ---------- Caption ----------
    d.send_keys(
        "Engagement Delivered with @influensor.in by @blackaquaindia.in",
        clear=False
    )
    d.press("enter")
    time.sleep(1)

    # 4️⃣ Your story
    if not retry_step(
        "Your story",
        retries=5,
        delay=2,
        fn=lambda: (
            d(textContains="Your story").exists(timeout=10)
            and d(textContains="Your story").click() is None
        )
    ):
        return False
    
    time.sleep(1)
    d.press("back")
    print(f"[{device_id}] Shared to story ✅")
    time.sleep(30)
    return True
