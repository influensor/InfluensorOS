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
TEST_USERNAME = "iamsonalbhardwaj"
POST_URLS = [
    "https://www.instagram.com/reel/C2KQLNHJ1FY/",
    "https://www.instagram.com/reel/DLPlTqpTQjF/",
    "https://www.instagram.com/reel/DQrHLn6E0r3/",
    "https://www.instagram.com/reel/DWRFUEZE_lq/",
    "https://www.instagram.com/reel/DWOWsC2E898/",
    "https://www.instagram.com/reel/DWGw9x4kxut/",
    "https://www.instagram.com/reel/DV8cpCqE_Xz/",
    "https://www.instagram.com/reel/DV0txW_CNAJ/",
    "https://www.instagram.com/reel/DVvjvjRE0DS/",
    "https://www.instagram.com/reel/DVqaweakwvX/",
    "https://www.instagram.com/reel/DVgG6leE59Z/",
    "https://www.instagram.com/reel/DVYZWTJE02Y/",
]

# =========================
# 🎯 CONTROL PANELS
# =========================
#PROFILE_ACTIONS = ["story","follow","message"]
#POST_ACTIONS = ["like","comment","gif_comment","save","share","repost","interested"]

PROFILE_ACTIONS = []
POST_ACTIONS = ["like", "comment", "save", "share", "repost", "interested"]

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

    # -------------------------
    # 1️⃣ LIKE (break condition)
    # -------------------------
    if "like" in POST_ACTIONS:
        liked = like_post(device_id)

        if liked == "already_liked":
            log(device_id, "⚠ Already liked → breaking loop")
            return False

    # -------------------------
    # 2️⃣ COMMENT
    # -------------------------
    if "comment" in POST_ACTIONS:
        comment = load_random_comment()
        if comment:
            post_comment(device_id, comment)
    
    # -------------------------
    # 2️⃣ GIF COMMENT
    # -------------------------
    if "gif_comment" in POST_ACTIONS:
        post_gif_comment(device_id)

    # -------------------------
    # 3️⃣ SAVE
    # -------------------------
    if "save" in POST_ACTIONS and random.random() < 0.7:
        save_post(device_id)

    # -------------------------
    # 4️⃣ SHARE
    # -------------------------
    if "share" in POST_ACTIONS and random.random() < 0.6:
        share_post(device_id)

    # -------------------------
    # 5️⃣ REPOST
    # -------------------------
    if "repost" in POST_ACTIONS and random.random() < 0.4:
        repost_post(device_id)

    # -------------------------
    # 6️⃣ INTERESTED
    # -------------------------
    if "interested" in POST_ACTIONS and random.random() < 0.5:
        mark_post_interested(device_id)

    return True


# =========================
# PROFILE ACTIONS
# =========================
def perform_profile_actions(device_id):

    # Story
    if "story" in PROFILE_ACTIONS and random.random() < 0.8:
        story_view_like(device_id)

    # Follow
    if "follow" in PROFILE_ACTIONS:
        follow_user(device_id)

    # Message
    if "message" in PROFILE_ACTIONS:
        time.sleep(1)
        send_promotional_message(device_id)


# =========================
# MAIN DEMO FLOW
# =========================
def demo_device(device_id):
    log(device_id, "🚀 Demo Worker Started")

    try:
        # 1️⃣ Open Instagram
        if not open_instagram(device_id):
            log(device_id, "❌ Instagram failed")
            return

        # 2️⃣ Open Profile
        if not ui_open_profile_by_username(device_id, TEST_USERNAME):
            log(device_id, "❌ Profile open failed")
            return

        time.sleep(1)

        # 3️⃣ PROFILE ACTIONS
        perform_profile_actions(device_id)

        # 4️⃣ RANDOM UNIQUE POSTS
        posts = random.sample(POST_URLS, min(MAX_POSTS, len(POST_URLS)))

        for i, post in enumerate(posts):
            log(device_id, f"▶ Opening Post {i+1}")

            if not open_post_by_url(device_id, post, TEST_USERNAME):
                log(device_id, "⚠ Post open failed → skipping")
                continue

            time.sleep(1)

            should_continue = perform_post_actions(device_id)

            if not should_continue:
                break

            time.sleep(random.uniform(1, 5))

        # 5️⃣ SWITCH ACCOUNT (ONCE)
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
        t = threading.Thread(target=demo_device, args=(device_id,), daemon=True)
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
