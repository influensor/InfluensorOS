import time
import random
import threading
from datetime import datetime

from engine.ui.instagram import open_instagram, ui_open_profile_by_username, open_post_by_url
from engine.ui.story_view_like import story_view_like
from engine.ui.like import like_post
from engine.ui.comment import post_comment
from engine.ui.gif import post_gif_comment
from engine.ui.repost import repost_post
from engine.ui.share import share_post
from engine.ui.save import save_post
from engine.ui.interested import mark_post_interested
from engine.ui.follow import follow_user
from engine.ui.message import send_promotional_message
from engine.ui.switch_account import switch_account

from engine.logic.comment_loader import load_random_comment


# =========================
# CONFIG
# =========================
MAX_POSTS = 5

TEST_USERNAME = "ilahabysanya"

POST_URLS = [
    "https://www.instagram.com/reel/DPjQokkE1nYP5hhAdhVn2nPXL2bA9h61rDbSWM0/",
    "https://www.instagram.com/reel/DWBeNexjBaq/",
    "https://www.instagram.com/reel/DV3N_NsDL8q/",
    "https://www.instagram.com/reel/DVqe-uyDJ3f/",
    "https://www.instagram.com/reel/DV8jC5xiapG/",
    "https://www.instagram.com/reel/DVYfqPxCXhe/",
    "https://www.instagram.com/reel/DVJM4ZaibDS/",
    "https://www.instagram.com/reel/DVf3aiPDKUE/",
    "https://www.instagram.com/reel/DUQQEvsiV3j/",
    "https://www.instagram.com/reel/DUUx9RJCUWe/",
    "https://www.instagram.com/reel/DUakGYzidar/",
]


# =========================
# LOGGER
# =========================
def log(device_id, msg):
    t = datetime.now().strftime("%H:%M:%S")
    line = f"[{t}] [{device_id}] {msg}"
    print(line)

    with open(f"demo_{device_id}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# =========================
# POST ACTIONS
# =========================
def perform_post_actions(device_id):
    """
    Perform all actions on a post.
    Break if already liked.
    """

    # -------------------------
    # 1️⃣ LIKE (break condition)
    # -------------------------
    liked = like_post(device_id)

    if liked == "already_liked":
        log(device_id, "⚠ Already liked → breaking loop")
        return False

    # -------------------------
    # 2️⃣ COMMENT
    # -------------------------
    comment = load_random_comment()
    if comment:
        post_comment(device_id, comment)
    
    # -------------------------
    # 2️⃣ GIF COMMENT
    # -------------------------
    post_gif_comment(device_id)
    
    # -------------------------
    # 3️⃣ SAVE
    # -------------------------
    save_post(device_id)

    # -------------------------
    # 4️⃣ SHARE
    # -------------------------
    share_post(device_id)

    # -------------------------
    # 5️⃣ REPOST
    # -------------------------
    repost_post(device_id)

    # -------------------------
    # 6️⃣ INTERESTED
    # -------------------------
    mark_post_interested(device_id)

    return True


# =========================
# MAIN DEMO FLOW
# =========================
def demo_device(device_id):
    log(device_id, "🚀 Demo Worker Started")

    try:
        # -------------------------
        # 1️⃣ Open Instagram
        # -------------------------
        if not open_instagram(device_id):
            log(device_id, "❌ Instagram failed")
            return

        # -------------------------
        # 2️⃣ Open Profile
        # -------------------------
        if not ui_open_profile_by_username(device_id, TEST_USERNAME):
            log(device_id, "❌ Profile open failed")
            return

        time.sleep(2)

        # -------------------------
        # 3️⃣ Story View (optional)
        # -------------------------
        if random.random() < 0.8:
            story_view_like(device_id)

        # -------------------------
        # 4️⃣ Follow
        # -------------------------
        follow_user(device_id)

        # -------------------------
        # 5️⃣ Message (with delay)
        # -------------------------
        time.sleep(2)
        send_promotional_message(device_id)

        # -------------------------
        # 6️⃣ RANDOM 5 UNIQUE POSTS
        # -------------------------
        posts = random.sample(POST_URLS, min(MAX_POSTS, len(POST_URLS)))

        for i, post in enumerate(posts):
            log(device_id, f"▶ Opening Post {i+1}")

            if not open_post_by_url(device_id, post, TEST_USERNAME):
                log(device_id, "⚠ Post open failed → skipping")
                continue

            time.sleep(2)

            # Perform actions
            should_continue = perform_post_actions(device_id)

            if not should_continue:
                break

            time.sleep(random.uniform(2, 4))

        # -------------------------
        # 7️⃣ Switch Account (ONLY ONCE)
        # -------------------------
        switch_account(device_id)

        log(device_id, "🎯 Demo Worker Completed")

    except Exception as e:
        log(device_id, f"🔥 CRASH → {e}")


# =========================
# RUN ALL DEVICES
# =========================
def run_demo_all_devices(device_ids):
    threads = []

    for device_id in device_ids:
        t = threading.Thread(
            target=demo_device,
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
        print("❌ No devices")
    else:
        print(f"✅ Devices: {devices}")
        run_demo_all_devices(devices)