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

def open_post_by_url(device_id, post_url):
    d = get_device(device_id)

    # Use Android intent to deep-link the post
    d.shell([
        "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", post_url
    ])

    time.sleep(6)  # allow reel/post to load
