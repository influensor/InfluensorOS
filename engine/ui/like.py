import time
import uiautomator2 as u2

# =========================
# LIKE EXECUTION ONLY
# =========================
def like_post(device_id, retries=2):
    """
    Tries to like the currently opened post/reel.
    Assumes caller already decided that liking is allowed.
    Returns True if like succeeded, else False.
    """

    d = u2.connect(device_id)

    for attempt in range(retries):
        # Try standard Like button
        if d(description="Like").exists(timeout=2):
            d(description="Like").click()
            time.sleep(1)

            # Verify like success
            if d(description="Unlike").exists(timeout=1):
                return True

        # Small retry delay
        time.sleep(1)

    return False
