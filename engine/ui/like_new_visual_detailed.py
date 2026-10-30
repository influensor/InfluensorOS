import re
import time
import xml.etree.ElementTree as ET

import uiautomator2 as u2

from engine.logger import info, warn, error


LIKE_BUTTON_IDS = [
    "com.instagram.android:id/like_button",
    "com.instagram.android:id/row_feed_button_like",
    "com.instagram.android:id/like_icon",
    "com.instagram.android:id/clips_like_button",
]

LIKE_COUNT_ID = "com.instagram.android:id/like_count"

# Minimum number of red pixels needed to identify Instagram's filled heart.
RED_MIN_PIXELS = 25


def _parse_like_count(value):
    """Parse 'Like number is 64', '1,234', '1.2K', etc."""
    if value is None:
        return None

    match = re.search(
        r"(\d[\d,]*(?:\.\d+)?)\s*([KMB])?",
        str(value).strip(),
        re.IGNORECASE,
    )
    if not match:
        return None

    try:
        number = float(match.group(1).replace(",", ""))
    except (TypeError, ValueError):
        return None

    multiplier = {
        "": 1,
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000,
    }.get((match.group(2) or "").upper(), 1)

    return int(number * multiplier)


def _read_like_count(device):
    """Read the visible like count from Instagram's accessibility node."""
    try:
        node = device(resourceId=LIKE_COUNT_ID)
        if node.exists(timeout=0.5):
            data = node.info or {}
            count = _parse_like_count(data.get("contentDescription"))
            if count is None:
                count = _parse_like_count(data.get("text"))
            if count is not None:
                return count
    except Exception:
        pass

    try:
        root = ET.fromstring(device.dump_hierarchy())
        for node in root.iter("node"):
            if node.attrib.get("resource-id") == LIKE_COUNT_ID:
                count = _parse_like_count(node.attrib.get("content-desc"))
                if count is None:
                    count = _parse_like_count(node.attrib.get("text"))
                if count is not None:
                    return count
    except Exception:
        pass

    return None


def _find_like_button(device):
    for resource_id in LIKE_BUTTON_IDS:
        try:
            button = device(resourceId=resource_id)
            if button.exists(timeout=0.5):
                return button
        except Exception:
            continue
    return None


def check_like_state_new(device, like_button=None):
    """
    NEW detector: inspect the heart's screenshot pixels.

    Returns:
        True  = filled red heart (liked)
        False = white outline heart (unliked)
        None  = unable to classify safely
    """
    if like_button is None:
        like_button = _find_like_button(device)

    if like_button is None:
        return None

    try:
        bounds = (like_button.info or {}).get("bounds")
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
            # Solid red/pink heart; the unliked heart is a white outline.
            if (
                red >= 170
                and green <= 105
                and blue <= 145
                and (red - green) >= 75
            ):
                red_pixels += 1
                if red_pixels >= RED_MIN_PIXELS:
                    return True

        return False

    except Exception:
        return None


def check_like_state_old(device, like_button=None):
    """
    OLD detector: use uiautomator2's selected state, as in the original code.

    Returns:
        True  = selected (liked)
        False = not selected (unliked)
        None  = button/state unavailable
    """
    if like_button is None:
        like_button = _find_like_button(device)

    if like_button is None:
        return None

    try:
        button_info = like_button.info or {}
        if "selected" not in button_info:
            return None
        return bool(button_info.get("selected"))
    except Exception:
        return None


def is_post_liked(device, like_button=None, log_result=True):
    """
    Combine both detectors.

    If EITHER detector returns True, the post is considered liked.
    We only consider the post safely unliked when BOTH detectors explicitly
    return False. Any unknown result without a True result is inconclusive.
    """
    if like_button is None:
        like_button = _find_like_button(device)

    if like_button is None:
        return None

    new_state = check_like_state_new(device, like_button)
    old_state = check_like_state_old(device, like_button)

    if log_result:
        info(
            f"🔎 Like detectors | NEW visual={new_state} | OLD selected={old_state}"
        )

    # Either detector can protect an already-liked post.
    if new_state is True or old_state is True:
        return True

    # Only click when both detectors positively report unliked.
    if new_state is False and old_state is False:
        return False

    return None


def like_post(device_id, retries=2, verify_timeout=8, poll_interval=0.5):
    """
    Safely like the currently opened Instagram post/reel.

    Flow:
      1. NEW visual detector checks the heart.
      2. OLD selected-state detector checks the button.
      3. If EITHER says liked, skip the click and return True.
      4. Click exactly once only if BOTH say unliked.
      5. Poll both detectors after clicking; EITHER returning True confirms
         the liked state.
      6. The like count is logged as supporting information, not used alone
         to decide liked state.

    `retries` is retained for compatibility with existing callers. The click
    itself is never retried because a second click can unlike the post.
    """
    try:
        device = u2.connect(device_id)
    except Exception as exc:
        error(f"❌ Could not connect to device: {exc}", device_id)
        return False

    info("▶ Like Post - checking NEW and OLD like-state detectors", device_id)

    like_button = _find_like_button(device)
    if like_button is None:
        error("❌ Like button not found", device_id)
        return False

    # Run both detectors before taking any action.
    initial_state = is_post_liked(device, like_button)

    if initial_state is True:
        info("✅ Already liked | At least one detector returned TRUE. Skipping click.", device_id)
        return True

    if initial_state is None:
        warn(
            "⚠️ Like state is inconclusive. At least one detector could not "
            "read the state, and neither confirmed liked. Skipping click "
            "to prevent accidental unlike.",
            device_id,
        )
        return False

    info("♡ Both detectors report UNLIKED. Safe to click once.", device_id)

    before_count = _read_like_count(device)
    if before_count is not None:
        info(f"❤️ Like count before action: {before_count}", device_id)
    else:
        warn("⚠️ Like count unavailable; state verification will use both detectors.", device_id)

    # Exactly one click. Never blindly retry.
    try:
        like_button.click()
    except Exception as exc:
        error(f"❌ Like button click failed: {exc}", device_id)
        return False

    info("🖱️ Like clicked once. Verifying with both detectors...", device_id)

    deadline = time.monotonic() + max(0, verify_timeout)
    last_count = before_count

    while time.monotonic() < deadline:
        time.sleep(max(0.1, poll_interval))

        current_button = _find_like_button(device)
        if current_button is None:
            continue

        current_state = is_post_liked(
            device,
            current_button,
            log_result=False,
        )

        current_count = _read_like_count(device)
        if current_count is not None:
            last_count = current_count

        # Either NEW or OLD detector returning True means LIKED.
        if current_state is True:
            if before_count is not None and last_count is not None:
                increase = last_count - before_count
                info(
                    f"✅ Like successful | At least one detector says LIKED | "
                    f"Count: {before_count} → {last_count} ({increase:+d})",
                    device_id,
                )
            else:
                info(
                    "✅ Like successful | At least one detector says LIKED.",
                    device_id,
                )
            return True

    # Final state check. Never click a second time.
    final_button = _find_like_button(device)
    final_state = (
        is_post_liked(device, final_button, log_result=False)
        if final_button is not None
        else None
    )

    if final_state is True:
        info("✅ Reel is LIKED | Confirmed by at least one detector.", device_id)
        return True

    if final_state is False:
        warn(
            "⚠️ Both detectors still report UNLIKED after the click. "
            "No second click was attempted.",
            device_id,
        )
    else:
        warn(
            "⚠️ Final like state is inconclusive. No second click was attempted.",
            device_id,
        )

    return False
