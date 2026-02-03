import time
import random
import uiautomator2 as u2

# =========================
# PASSIVE VIEW / WATCH
# =========================
def view_post(device_id, min_seconds=1, max_seconds=60):
    """
    Passive view of a post or reel.
    No interaction, just watch time.
    """

    duration = random.randint(min_seconds, max_seconds)
    print(f"[{device_id}] Viewing post for {duration}s")

    d = u2.connect(device_id)

    start = time.time()

    while time.time() - start < duration:
        # Small random idle pauses to look human
        time.sleep(random.uniform(1.0, 2.5))

        # Optional micro-scroll (VERY subtle, safe)
        if random.random() < 0.2:
            try:
                d.swipe_ext("up", scale=0.05)
            except Exception:
                pass

    return True
