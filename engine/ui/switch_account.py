import time
import uiautomator2 as u2

INSTAGRAM_PKG = "com.instagram.android"
PROFILE_TAB_ID = "com.instagram.android:id/tab_avatar"
USERNAME_HEADER_ID = "com.instagram.android:id/action_bar_title"
INSTAGRAM_PROFILE_URL = "http://instagram.com/_u"


def switch_account(device_id):
    """
    Opens Instagram account switcher,
    clicks ONE valid account row,
    returns the username clicked.
    """

    d = u2.connect(device_id)
    
    # Open Instagram cleanly
    d.shell([
        "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", INSTAGRAM_PROFILE_URL,
        INSTAGRAM_PKG
    ])
    time.sleep(1)
    
    # Open profile tab
    if not d(resourceId=PROFILE_TAB_ID).exists(timeout=3):
        print(f"[{device_id}] Profile tab not found")
        return None

    d(resourceId=PROFILE_TAB_ID).click()
    time.sleep(2)

    # Open account switcher
    if not d(resourceId=USERNAME_HEADER_ID).exists(timeout=3):
        print(f"[{device_id}] Username header not found")
        return None

    d(resourceId=USERNAME_HEADER_ID).click()
    time.sleep(2)

    # Collect clickable rows
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
    time.sleep(3)

    return username
