import re
import time

import uiautomator2 as u2

from engine.logger import info, warn, error


LIKE_BUTTON_IDS = (
    "com.instagram.android:id/like_button",
    "com.instagram.android:id/row_feed_button_like",
    "com.instagram.android:id/like_icon",
    "com.instagram.android:id/clips_like_button",
)
LIKE_COUNT_ID = "com.instagram.android:id/like_count"

RED_MIN_PIXELS = 25


def _find_like_button(device):
    for resource_id in LIKE_BUTTON_IDS:
        button = device(resourceId=resource_id)
        if button.exists(timeout=0.5):
            return button
    return None


def _visual_like_state(device, button):
    """True=liked, False=unliked, None=unknown."""
    try:
        bounds = button.info["bounds"]
        image = device.screenshot().convert("RGB")

        left = max(0, int(bounds["left"]) + 5)
        top = max(0, int(bounds["top"]) + 5)
        right = min(image.width, int(bounds["right"]) - 5)
        bottom = min(image.height, int(bounds["bottom"]) - 5)

        red_pixels = 0
        for red, green, blue in image.crop(
            (left, top, right, bottom)
        ).getdata():
            if red >= 170 and green <= 105 and blue <= 145 and red - green >= 75:
                red_pixels += 1
                if red_pixels >= RED_MIN_PIXELS:
                    return True

        return False
    except Exception:
        return None


def _old_like_state(button):
    """Original uiautomator2 selected-state check."""
    try:
        return bool(button.info.get("selected", False))
    except Exception:
        return None


def _is_liked(device, button):
    """Either detector says True => liked; both False => unliked."""
    visual = _visual_like_state(device, button)
    selected = _old_like_state(button)

    if visual is True or selected is True:
        return True
    if visual is False and selected is False:
        return False
    return None


def _like_count(device):
    """Read the numeric like count from Instagram's like_count node."""
    try:
        node = device(resourceId=LIKE_COUNT_ID)
        if not node.exists(timeout=0.3):
            return None

        data = node.info or {}
        text = data.get("contentDescription") or data.get("text") or ""
        match = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*([KMB])?", str(text), re.I)
        if not match:
            return None

        number = float(match.group(1).replace(",", ""))
        multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
        return int(number * multiplier[(match.group(2) or "").upper()])
    except Exception:
        return None


def like_post(device_id, retries=2, verify_timeout=8, poll_interval=0.5):
    """
    Check liked state using BOTH methods:
      - NEW: screenshot heart colour.
      - OLD: uiautomator2 selected state.

    Either True means already liked. Click only when both return False.
    After clicking, either True confirms success. Never click twice.
    `retries` remains in the signature for compatibility.
    """
    try:
        device = u2.connect(device_id)
        button = _find_like_button(device)

        if button is None:
            error("❌ Like button not found", device_id)
            return False

        state = _is_liked(device, button)

        if state is True:
            info("✅ Already liked. Skipping click.", device_id)
            return True

        if state is None:
            warn("⚠️ Like state unclear. Skipping click for safety.", device_id)
            return False

        before = _like_count(device)
        info(f"♡ Unliked | Like count before click: {before}", device_id)

        # One click only. A second click could unlike the post.
        button.click()
        info("🖱️ Like clicked once. Verifying...", device_id)

        deadline = time.monotonic() + max(0, verify_timeout)
        while time.monotonic() < deadline:
            time.sleep(max(0.1, poll_interval))

            button = _find_like_button(device)
            if button is None:
                continue

            if _is_liked(device, button) is True:
                after = _like_count(device)
                if before is not None and after is not None:
                    info(
                        f"✅ Like successful | Count: {before} → {after} "
                        f"({after - before:+d})",
                        device_id,
                    )
                else:
                    info("✅ Like successful.", device_id)
                return True

        warn("⚠️ Like not confirmed. No second click attempted.", device_id)
        return False

    except Exception as exc:
        error(f"❌ Like error: {exc}", device_id)
        return False
