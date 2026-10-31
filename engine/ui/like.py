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

# Reel media container observed in the supplied Instagram XML.
# Feed media IDs vary by Instagram version; only use a known media container.
MEDIA_CONTAINER_IDS = [
    "com.instagram.android:id/clips_single_image_media_content",
    "com.instagram.android:id/clips_media_component",
    "com.instagram.android:id/media_group",
    "com.instagram.android:id/media_container",
]

RED_MIN_PIXELS = 25
DOUBLE_TAP_INTERVAL = 0.12
MEDIA_EDGE_MARGIN = 0.20


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
    """Visual detector: True=red filled heart, False=outline, None=unknown."""
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
            if red >= 170 and green <= 105 and blue <= 145 and red - green >= 75:
                red_pixels += 1
                if red_pixels >= RED_MIN_PIXELS:
                    return True
        return False
    except Exception:
        return None


def check_like_state_old(device, like_button=None):
    """Original accessibility detector using selected state."""
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
    """Either detector True=liked; both False=unliked; otherwise unknown."""
    if like_button is None:
        like_button = _find_like_button(device)
    if like_button is None:
        return None

    visual_state = check_like_state_new(device, like_button)
    old_state = check_like_state_old(device, like_button)

    if log_result:
        info(
            f"🔎 Like detectors | NEW visual={visual_state} | "
            f"OLD selected={old_state}"
        )

    if visual_state is True or old_state is True:
        return True
    if visual_state is False and old_state is False:
        return False
    return None


def _parse_bounds(bounds_text):
    """Convert XML bounds '[x1,y1][x2,y2]' to a bounds dictionary."""
    match = re.fullmatch(
        r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",
        bounds_text or "",
    )
    if not match:
        return None

    left, top, right, bottom = map(int, match.groups())
    if right <= left or bottom <= top:
        return None

    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
    }


def _find_media_tap_point(device, device_id=None):
    """
    Find a safe point inside the actual media container.

    It deliberately does not use the Like button bounds or arbitrary screen
    coordinates. If no recognized media container is present, return None.
    """
    try:
        root = ET.fromstring(device.dump_hierarchy())
        candidates = []

        for node in root.iter("node"):
            resource_id = node.attrib.get("resource-id", "")
            if resource_id not in MEDIA_CONTAINER_IDS:
                continue

            bounds = _parse_bounds(node.attrib.get("bounds"))
            if not bounds:
                continue

            width = bounds["right"] - bounds["left"]
            height = bounds["bottom"] - bounds["top"]

            # Ignore tiny or unusually narrow containers.
            if width < 250 or height < 250:
                continue

            # Prefer the specific media-content node over its larger parent.
            priority = MEDIA_CONTAINER_IDS.index(resource_id)
            area = width * height
            candidates.append((priority, -area, bounds, resource_id))

        if not candidates:
            return None

        # Prefer the most specific recognized media container.
        candidates.sort(key=lambda item: (item[0], item[1]))
        _, _, bounds, resource_id = candidates[0]

        width = bounds["right"] - bounds["left"]
        height = bounds["bottom"] - bounds["top"]

        # Use a point in the central media area, away from edges and controls.
        x = bounds["left"] + width // 2
        y = bounds["top"] + height // 2

        # Confirm the point is not inside any separate clickable child control.
        for node in root.iter("node"):
            if node.attrib.get("clickable") != "true":
                continue

            child_bounds = _parse_bounds(node.attrib.get("bounds"))
            if not child_bounds:
                continue

            # Ignore the media container itself and large clickable ancestors.
            if (
                child_bounds["left"] <= bounds["left"]
                and child_bounds["top"] <= bounds["top"]
                and child_bounds["right"] >= bounds["right"]
                and child_bounds["bottom"] >= bounds["bottom"]
            ):
                continue

            if (
                child_bounds["left"] <= x <= child_bounds["right"]
                and child_bounds["top"] <= y <= child_bounds["bottom"]
            ):
                warn(
                    "⚠️ Media center overlaps another clickable UI element. "
                    "Refusing to double-tap.",
                    device_id,
                )
                return None

        info(
            f"🎯 Double-tap media point ({x}, {y}) "
            f"from {resource_id}", device_id
        )
        return x, y

    except Exception as exc:
        warn(f"⚠️ Could not locate safe media area: {exc}", device_id)
        return None


def _double_tap_media(device, x, y):
    """Double-tap media coordinates, never the Like UI button."""
    device.click(x, y)
    time.sleep(DOUBLE_TAP_INTERVAL)
    device.click(x, y)


def like_post(device_id, retries=2, verify_timeout=8, poll_interval=0.5):
    """
    Like the currently opened Instagram post/reel.

    Exact action sequence:
      1. Check current state. If already liked, do nothing.
      2. Locate a safe media tap point before changing anything.
      3. Click the Instagram Like UI element exactly once.
      4. Double-tap the safe visible media area exactly once.
      5. Verify the final liked state using visual + accessibility detectors.

    `retries` is retained for compatibility. Neither action is blindly retried.
    """
    try:
        device = u2.connect(device_id)
    except Exception as exc:
        error(f"❌ Could not connect to device: {exc}", device_id)
        return False

    info("▶ Like Post - checking current like state", device_id)

    like_button = _find_like_button(device)
    if like_button is None:
        error("❌ Like button not found", device_id)
        return False

    initial_state = is_post_liked(device, like_button)

    if initial_state is True:
        info("✅ Already liked. Skipping all like actions.", device_id)
        return True

    if initial_state is None:
        warn(
            "⚠️ Like state is inconclusive. Skipping actions for safety.",
            device_id,
        )
        return False

    # Resolve the media point BEFORE clicking the Like button. This avoids
    # performing only the first half of the requested sequence.
    tap_point = _find_media_tap_point(device, device_id)
    if tap_point is None:
        warn("⚠️ Safe media area not found. No like action performed.", device_id)
        return False

    before_count = _read_like_count(device)
    if before_count is not None:
        info(f"❤️ Like count before action: {before_count}", device_id)

    # ACTION 1: click the actual Instagram Like UI element once.
    try:
        like_button.click()
    except Exception as exc:
        error(f"❌ Like UI button click failed: {exc}", device_id)
        return False

    info("🖱️ Step 1/2: Like UI element clicked once.", device_id)

    # Allow Instagram to process the button click before the media gesture.
    time.sleep(0.35)

    # ACTION 2: double-tap the safe media area once.
    # Per the user's confirmed behavior, this gesture does not unlike the post.
    try:
        _double_tap_media(device, *tap_point)
    except Exception as exc:
        error(
            f"❌ Step 2/2: Media double-tap failed after UI click: {exc}",
            device_id,
        )
        # Do not click again: the UI click may already have liked the post.
        return False

    info(
        f"🖱️ Step 2/2: Media double-tapped once at {tap_point}. "
        "Verifying final state...",
        device_id,
    )

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

        if current_state is True:
            if before_count is not None and last_count is not None:
                info(
                    f"✅ Like successful | Count: {before_count} → "
                    f"{last_count} ({last_count - before_count:+d})",
                    device_id,
                )
            else:
                info(
                    "✅ Like successful | Confirmed by visual/accessibility state.",
                    device_id,
                )
            return True

    final_button = _find_like_button(device)
    final_state = (
        is_post_liked(device, final_button, log_result=False)
        if final_button is not None
        else None
    )

    if final_state is True:
        info("✅ Post is liked | Confirmed after verification timeout.", device_id)
        return True

    warn(
        "⚠️ Like was not confirmed after UI click + media double-tap. "
        "No action was repeated.",
        device_id,
    )
    return False
