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
    Full-button RGB-range detector:
      True  = filled red heart detected (liked)
      False = filled red heart not detected (unliked)
      None  = unable to inspect
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

        # Scan the complete Like button bounds.
        left = max(0, int(bounds["left"]))
        top = max(0, int(bounds["top"]))
        right = min(width, int(bounds["right"]))
        bottom = min(height, int(bounds["bottom"]))

        if right <= left or bottom <= top:
            return None

        pixels = list(screenshot.crop((left, top, right, bottom)).getdata())
        if not pixels:
            return None

        red_pixels = sum(
            1 for red, green, blue in pixels
            if (
                235 <= red <= 255
                and 10 <= green <= 65
                and 25 <= blue <= 90
            )
        )

        red_ratio = red_pixels / len(pixels)
        return red_pixels >= 25 and red_ratio >= 0.08

    except Exception:
        return None

def _check_old_like_state(button):
    """XML detector using Instagram's selected accessibility attribute."""
    try:
        info = button.info or {}
        if "selected" not in info:
            return None
        return bool(info["selected"])
    except Exception:
        return None

def _is_any_like_button_liked(device):
    """
    Either detector returning True means LIKED.
    Both detectors must return False to confirm UNLIKED.
    None means inconclusive.
    """
    button = _find_like_button(device)
    if button is None:
        return None

    visual_state = _check_visual_like_state(device, button)
    xml_state = _check_old_like_state(button)

    if visual_state is True or xml_state is True:
        return True
    if visual_state is False and xml_state is False:
        return False
    return None


# =========================
# POST STATE CHECK
# =========================

def is_post_liked(device_id, retries=5, delay=1.0):
    """
    Check the currently opened post/reel using both detection methods.

    Returns True if either method confirms liked.
    Returns False only when both detectors confirm unliked.
    Returns True when either confirms liked or state remains unknown
    after retries, so engagement actions are skipped safely.
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

    # Unknown state must never be treated as unliked.
    return True


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
