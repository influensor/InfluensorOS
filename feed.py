import time
import random
import threading
from datetime import datetime
from engine.ui.like import like_post
from engine.ui.comment import post_comment
from engine.ui.gif import post_gif_comment
from engine.ui.save import save_post
from engine.ui.share import share_post
from engine.ui.repost import repost_post
from engine.ui.interested import mark_post_interested
from engine.ui.switch_account import switch_account
from engine.logic.comment_loader import load_random_comment
from engine.ui.device import get_device


# =========================
# CONFIG
# =========================
LOOP_COUNT = 1

POST_ACTIONS = [
    "like",
    "comment",
    "gif_comment",
    "save",
    "share",
    "repost",
    "interested"
]


# =========================
# LOGGER
# =========================
def log(device_id, msg):
    t = datetime.now().strftime("%H:%M:%S")
    line = f"[{t}] [{device_id}] {msg}"
    print(line)

    with open(f"opened_reel_{device_id}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# =========================
# DELAY
# =========================
def delay(a=0.5, b=1.5):
    time.sleep(random.uniform(a, b))


# =========================
# ACTIONS ON OPENED REEL
# =========================
def perform_actions(device_id):

    # LIKE
    if "like" in POST_ACTIONS:
        like_post(device_id)
        delay()

    # COMMENT / GIF
    if "comment" in POST_ACTIONS:
        comment = load_random_comment()
        if comment:
            post_comment(device_id, comment)

    if "gif_comment" in POST_ACTIONS:
        post_gif_comment(device_id)

    delay(1, 2)

    # SAVE
    if "save" in POST_ACTIONS and random.random() < 0.7:
        save_post(device_id)
        delay()

    # SHARE
    if "share" in POST_ACTIONS and random.random() < 0.5:
        share_post(device_id)
        delay()

    # REPOST
    if "repost" in POST_ACTIONS and random.random() < 0.3:
        repost_post(device_id)
        delay()

    # INTERESTED
    if "interested" in POST_ACTIONS and random.random() < 0.5:
        mark_post_interested(device_id)
        delay()


# =========================
# DEVICE WORKER
# =========================
def opened_reel_device(device_id):
    log(device_id, "🚀 Opened Reel Worker Started")

    try:
        # 2️⃣ LOOP ACTIONS
        for i in range(LOOP_COUNT):
            log(device_id, f"▶ Action Cycle {i+1}")

            perform_actions(device_id)

            time.sleep(random.uniform(2, 3))

        # 3️⃣ Switch account END
        switch_account(device_id)

        log(device_id, "🎯 Worker Completed")

    except Exception as e:
        log(device_id, f"🔥 CRASH → {e}")


# =========================
# MULTI DEVICE RUNNER
# =========================
def run_all_devices(device_ids):
    threads = []

    for device_id in device_ids:
        t = threading.Thread(
            target=opened_reel_device,
            args=(device_id,),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    from engine.logic.device_auth import get_connected_adb_devices

    devices = get_connected_adb_devices()

    if not devices:
        print("❌ No devices connected")
    else:
        print(f"✅ Devices: {devices}")
        run_all_devices(devices)