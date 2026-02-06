import time
import random
from engine.ui.device import get_device

from engine.logger import info, warn, error


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
                time.sleep(random.uniform(1.0, 2.5))

                # Optional micro-scroll (very subtle)
                if random.random() < 0.2:
                    try:
                        d.swipe_ext("up", scale=10)
                        time.sleep(random.uniform(1.0, 3.0))
                        d.swipe_ext("down", scale=10)
                    except Exception:
                        pass

            info(f"✅ View completed ({duration}s)", device_id)
            return True

        except Exception as e:
            warn(f"⚠ View error: {e}", device_id)
            time.sleep(1)

    error("❌ View failed", device_id)
    return False
