import time
from engine.ui.device import get_device

from engine.logger import info, warn, error


INSTAGRAM_PKG = "com.instagram.android"
INSTAGRAM_PROFILE_URL = "http://instagram.com/_u"
PROFILE_ICON_XPATH = '//*[@content-desc="Profile"]'


# =========================
# SWITCH ACCOUNT
# =========================
def switch_account(device_id, retries=2):
    """
    Opens Instagram profile, long-presses profile icon,
    switches to next available account.
    Returns switched username or None.
    """

    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Switch Account (attempt {attempt})", device_id)

        # -----------------------------
        # Open Instagram Profile Page
        # -----------------------------
        d.shell([
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", INSTAGRAM_PROFILE_URL,
            INSTAGRAM_PKG
        ])
        time.sleep(1)

        # -----------------------------
        # Wait for profile icon
        # -----------------------------
        profile_icon = d.xpath(PROFILE_ICON_XPATH)
        if not profile_icon.wait(timeout=5):
            warn("⚠ Profile icon not found", device_id)
            time.sleep(1)
            continue

        # -----------------------------
        # 1️⃣ Long press profile icon
        # -----------------------------
        profile_icon.long_click()
        time.sleep(1)

        # -----------------------------
        # Swipe up inside account switcher
        # -----------------------------
        w, h = d.window_size()
        d.swipe(w // 2, int(h * 0.8), w // 2, int(h * 0.2), 0.05)
        time.sleep(1)

        # -----------------------------
        # Collect valid account rows
        # -----------------------------
        rows = d(className="android.view.ViewGroup", clickable=True)
        valid_rows = []

        for r in rows:
            desc = (r.info.get("contentDescription") or "").lower()

            if not desc:
                continue
            if "add instagram account" in desc:
                continue
            if "accounts centre" in desc:
                continue

            valid_rows.append(r)

        if not valid_rows:
            warn("⚠ No valid account rows", device_id)
            d.press("back")
            time.sleep(1)
            continue

        # -----------------------------
        # Click NEXT account (last row)
        # -----------------------------
        target = valid_rows[-1]

        username = None
        desc = target.info.get("contentDescription")
        if desc:
            username = desc.split(",")[0].strip()

        # Fallback: child text
        if not username:
            for t in target.xpath(".//android.view.View").all():
                if t.text:
                    username = t.text.strip()
                    break

        target.click()
        time.sleep(1)

        info(f"✅ Switched account → {username}", device_id)
        return username

    error("❌ Switch account failed after retries", device_id)
    return None
