import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn


# =========================
# SELECTORS
# =========================
FOLLOW_SELECTORS = [
    {"text": "Follow"},
    {"description": "Follow"},
]

FOLLOWING_SELECTORS = [
    {"text": "Following"},
    {"description": "Following"},
]

REQUESTED_SELECTORS = [
    {"text": "Requested"},
    {"description": "Requested"},
]


# =========================
# HELPER: FIND UI
# =========================
def _find_ui(d, selectors, timeout=2):
    for sel in selectors:
        obj = d(**sel)
        if obj.exists(timeout=timeout):
            return obj
    return None


# =========================
# MAIN FUNCTION
# =========================
def follow_user(device_id):
    """
    Click follow button if available on profile screen.

    Returns:
        True → followed or already following
        False → failed / not found
    """

    d = get_device(device_id)

    try:
        # -------------------------
        # 1️⃣ Already Following?
        # -------------------------
        following_btn = _find_ui(d, FOLLOWING_SELECTORS)

        if following_btn:
            info("Already following", device_id)
            return True

        requested_btn = _find_ui(d, REQUESTED_SELECTORS)

        if requested_btn:
            info("Follow already requested", device_id)
            return True

        # -------------------------
        # 2️⃣ Find Follow Button
        # -------------------------
        follow_btn = _find_ui(d, FOLLOW_SELECTORS)

        if not follow_btn:
            warn("Follow button not found", device_id)
            return False

        # -------------------------
        # 3️⃣ Click Follow
        # -------------------------
        follow_btn.click()
        time.sleep(random.uniform(1.0, 2.0))

        info("Follow clicked", device_id)

        # -------------------------
        # 4️⃣ Verify (optional)
        # -------------------------
        if _find_ui(d, FOLLOWING_SELECTORS, timeout=2) or \
           _find_ui(d, REQUESTED_SELECTORS, timeout=2):
            info("Follow successful (verified)", device_id)
            return True

        warn("Follow may not be confirmed", device_id)
        return True

    except Exception as e:
        warn(f"Follow error: {e}", device_id)
        return False