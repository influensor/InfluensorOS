import time
import random
from engine.ui.device import get_device
from engine.logger import info, warn, error
from engine.ui.swipe import swipe_up
from engine.ui.swipe import swipe_down


# =========================
# PASSIVE VIEW / WATCH
# =========================
def view_post(device_id, min_seconds=1, max_seconds=60, retries=1):
    """
    Passive view of a post or reel.
    No interaction, just watch time.
    """

    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        duration = random.randint(min_seconds, max_seconds)
        info(f"▶ View Post (attempt {attempt}) → {duration}s", device_id)

        try:
            start = time.time()
            while time.time() - start < duration:
                # Human-like idle pause
                time.sleep(random.uniform(1, 3))
                try:
                    swipe_up(device_id)
                    time.sleep(random.uniform(2, 2))
                    swipe_down(device_id)
                except Exception:
                    pass

            info(f"✅ View completed ({duration}s)", device_id)
            return True

        except Exception as e:
            warn(f"⚠ View error: {e}", device_id)
            time.sleep(1)

    error("❌ View failed", device_id)
    return False
