import time
import uiautomator2 as u2

INSTAGRAM_PKG = "com.instagram.android"
INSTAGRAM_PROFILE_URL = "http://instagram.com/_u"
PROFILE_TAB_ID = "com.instagram.android:id/tab_avatar"
PROFILE_ICON_XPATH = '//*[@content-desc="Profile"]'


def switch_account(device):
    d = u2.connect(device)

    # -----------------------------
    # Open Instagram Home Page
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
        print(f"[{device}] ❌ Profile icon not found")
        return None

    # -----------------------------
    # 1️⃣ LONG PRESS ONLY
    # -----------------------------
    d.xpath(profile_icon).long_click()
    time.sleep(1)
    
    # --- Swipe up inside account switcher ---
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
        print(f"[{device_id}] No valid account rows")
        d.press("back")
        return None

    # Click NEXT account (last row)
    target = valid_rows[-1]

    username = None
    desc = target.info.get("contentDescription")
    if desc:
        username = desc.split(",")[0].strip()

    if not username:
        # fallback: search child text
        for t in target.xpath(".//android.view.View").all():
            if t.text:
                username = t.text.strip()
                break

    target.click()
    time.sleep(1)

    return username
