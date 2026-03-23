import time
import random
from engine.ui.device import get_device
from engine.ui.reel_commenter import reel_commenter
from engine.ui.swipe import swipe_up

def reel_comment_loop(device_id, total_reels=5):
    """
    Loop:
    comment → swipe → repeat
    """
    d = get_device(device_id)
    print(f"[{device_id}] 🔁 Starting Reel Comment Loop ({total_reels})")

    for i in range(total_reels):
        print(f"[{device_id}] ▶ Reel {i+1}/{total_reels}")

        # -------------------------
        # 1️⃣ Comment on current reel
        # -------------------------
        success = reel_commenter(device_id)

        if not success:
            print(f"[{device_id}] ⚠ Comment failed, still swiping")

        # -------------------------
        # 2️⃣ Watch (important for realism)
        # -------------------------
        watch_time = random.uniform(1, 10)
        time.sleep(watch_time)

        # -------------------------
        # 3️⃣ Swipe to next reel
        # -------------------------
        swipe_up(device_id)

    print(f"[{device_id}] ✅ Reel comment loop completed")
    return True