import time
from engine.ui.device import get_device

INSTAGRAM_PKG = "com.instagram.android"

def open_instagram(device_id):
    d = get_device(device_id)

    # Stop app if running
    d.app_stop(INSTAGRAM_PKG)
    time.sleep(1)

    # Start Instagram
    d.app_start(INSTAGRAM_PKG)
    time.sleep(5)

def open_profile_by_username(device_id, username):
    import subprocess

    url = f"https://www.instagram.com/{username}/"

    subprocess.run([
        "adb", "-s", device_id,
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", url,
        "-p", INSTAGRAM_PKG
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)  # allow profile to load

def open_post_by_url(device_id, post_url):
    import subprocess

    subprocess.run([
        "adb", "-s", device_id,
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", post_url,
        "-p", INSTAGRAM_PKG
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)  # allow reel/post to load

