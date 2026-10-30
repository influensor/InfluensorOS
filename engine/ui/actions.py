import time

import uiautomator2 as u2


# =========================
# LIKE BUTTON SELECTORS
# =========================

LIKE_SELECTORS = [
    {"resourceId": "com.instagram.android:id/like_button"},
    {"resourceId": "com.instagram.android:id/row_feed_button_like"},
    {"resourceId": "com.instagram.android:id/like_icon"},
    {"resourceId": "com.instagram.android:id/clips_like_button"},
]

RED_MIN_PIXELS = 25


def _find_like_button(device):
    """Return the first visible like button on the current screen."""
    for selector in LIKE_SELECTORS:
        try:
            button = device(**selector)
            if button.exists(timeout=0.5):
                return button
        except Exception:
            continue
    return None


def _check_visual_like_state(device, button):
    """
    NEW detector:
      True  = filled red heart (liked)
      False = white outline heart (unliked)
      None  = unable to inspect/classify
    """
    try:
        bounds = (button.info or {}).get("bounds")
        if not isinstance(bounds, dict):
            return None

        screenshot = device.screenshot()
        if screenshot is None:
            return None

        screenshot = screenshot.convert("RGB")
        width, height = screenshot.size

        left = max(0, int(bounds["left"]) + 5)
        top = max(0, int(bounds["top"]) + 5)
        right = min(width, int(bounds["right"]) - 5)
        bottom = min(height, int(bounds["bottom"]) - 5)

        if right <= left or bottom <= top:
            return None

        red_pixels = 0
        for red, green, blue in screenshot.crop(
            (left, top, right, bottom)
        ).getdata():
            if red >= 170 and green <= 105 and blue <= 145 and red - green >= 75:
                red_pixels += 1
                if red_pixels >= RED_MIN_PIXELS:
                    return True

        return False
    except Exception:
        return None


def _check_old_like_state(button):
    """
    OLD detector based on accessibility attributes:
    selected, checked, or activated.
    """
    try:
        info = button.info or {}
        if not info:
            return None
        return bool(
            info.get("selected")
            or info.get("checked")
            or info.get("activated")
        )
    except Exception:
        return None


def _is_any_like_button_liked(device):
    """
    Either detector returning True means LIKED.
    Only both detectors returning False means UNLIKED.
    None means inconclusive.
    """
    button = _find_like_button(device)
    if button is None:
        return None

    visual_state = _check_visual_like_state(device, button)
    old_state = _check_old_like_state(button)

    if visual_state is True or old_state is True:
        return True
    if visual_state is False and old_state is False:
        return False
    return None


# =========================
# POST STATE CHECK
# =========================

def is_post_liked(device_id, retries=5, delay=1.0):
    """
    Check the currently opened post/reel using both detection methods.

    Returns True if either method confirms liked.
    Returns False if both confirm unliked, or if state remains unknown
    after retries.
    """
    try:
        device = u2.connect(device_id)
    except Exception:
        return False

    for attempt in range(max(1, retries)):
        state = _is_any_like_button_liked(device)

        if state is True:
            return True
        if state is False:
            return False

        if attempt < retries - 1:
            time.sleep(delay)

    return False


# =========================
# DECISION GATE
# =========================

def should_skip_actions(device_id):
    """
    Returns:
        True  -> Post is already liked; skip further engagement actions.
        False -> Post is not detected as liked; continue normal action flow.
    """
    return is_post_liked(device_id)
