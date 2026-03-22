import time
import threading
from datetime import datetime
from engine.ui.instagram import (
    open_instagram,
    ui_open_profile_by_username,
    open_post_by_url
)
from engine.ui.story_view_like import story_view_like
from engine.ui.like import like_post
from engine.ui.comment import post_comment
from engine.ui.save import save_post
from engine.ui.share import share_post
from engine.ui.repost import repost_post
from engine.ui.switch_account import switch_account
from engine.ui.follow import follow_user
from engine.ui.message import send_promotional_message
from engine.ui.gif import post_gif_comment
from engine.logic.comment_loader import load_random_comment
from engine.ui.device import get_device


# =========================
# 🔥 CONTROL PANEL
# =========================

#ACTIONS = ["open_instagram", "profile", "follow", "message", "story", "post", "like", "comment", "gif_comment", "save", "share", "repost", "switch"]
ACTIONS = ["open_instagram", "profile"]

TEST_USERNAME = "ilahabysanya"
TEST_POST_URL = "https://www.instagram.com/reel/DQoEE3wAKL-/"

# =========================
# 📄 LOCAL DEBUG LOGGER
# =========================
def debug_log(device_id, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] [{device_id}] {message}"

    print(line)

    log_file = f"debug_{device_id}.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# =========================
# HELPER: RUN STEP
# =========================
def run_step(name, fn, device_id):
    debug_log(device_id, f"➡ {name}")

    try:
        result = fn()

        if result is False:
            raise Exception("Returned False")

        debug_log(device_id, f"✅ {name} SUCCESS")
        return True

    except Exception as e:
        debug_log(device_id, f"❌ {name} FAILED → {e}")

        # 📸 Screenshot on failure
        try:
            d = get_device(device_id)
            d.screenshot(f"debug_{device_id}_{name}.png")
        except:
            pass

        return False


# =========================
# DEVICE DEBUG FLOW
# =========================
def debug_device(device_id):
    debug_log(device_id, "🚀 Debug Worker Started")

    try:
        d = get_device(device_id)

        # -------------------------
        # 1️⃣ Open Instagram
        # -------------------------
        if "open_instagram" in ACTIONS:
            if not run_step(
                "Open Instagram",
                lambda: open_instagram(device_id),
                device_id
            ):
                return

        # -------------------------
        # 2️⃣ Open Profile
        # -------------------------
        if "profile" in ACTIONS:
            if not run_step(
                "Open Profile",
                lambda: ui_open_profile_by_username(device_id, TEST_USERNAME),
                device_id
            ):
                return

            time.sleep(2)  # 🔥 important for UI load

        # -------------------------
        # 3️⃣ FOLLOW USER
        # -------------------------
        if "follow" in ACTIONS:
            run_step(
                "Follow User",
                lambda: follow_user(device_id),
                device_id
            )
            time.sleep(1)

        # -------------------------
        # 4️⃣ SEND MESSAGE
        # -------------------------
        if "message" in ACTIONS:
            run_step(
                "Send Message",
                lambda: send_promotional_message(device_id),
                device_id
            )
            time.sleep(1)

        # -------------------------
        # 5️⃣ Story View Like
        # -------------------------
        if "story" in ACTIONS:
            run_step(
                "Story View Like",
                lambda: story_view_like(device_id),
                device_id
            )

        # -------------------------
        # 6️⃣ Open Post/Reel
        # -------------------------
        if "post" in ACTIONS:
            if not run_step(
                "Open Post",
                lambda: open_post_by_url(device_id, TEST_POST_URL, TEST_USERNAME),
                device_id
            ):
                return
            time.sleep(2)

        # -------------------------
        # 7️⃣ Like
        # -------------------------
        if "like" in ACTIONS:
            run_step(
                "Like",
                lambda: like_post(device_id),
                device_id
            )
            time.sleep(1)

        # -------------------------
        # 8️⃣ TEXT COMMENT
        # -------------------------
        if "comment" in ACTIONS:
            def comment_action():
                comment = load_random_comment()

                if not comment:
                    raise Exception("No comments found")

                debug_log(device_id, f"💬 Comment: {comment}")
                return post_comment(device_id, comment)

            run_step("Comment", comment_action, device_id)
            time.sleep(1)

        # -------------------------
        # 9️⃣ GIF COMMENT
        # -------------------------
        if "gif_comment" in ACTIONS:
            def gif_comment_action():
                debug_log(device_id, "🎬 Sending GIF Comment")
                return post_gif_comment(device_id)

            run_step("GIF Comment", gif_comment_action, device_id)
            time.sleep(1)

        # -------------------------
        # 🔟 Save
        # -------------------------
        if "save" in ACTIONS:
            run_step(
                "Save",
                lambda: save_post(device_id),
                device_id
            )
            time.sleep(1)

        # -------------------------
        # 1️⃣1️⃣ Share
        # -------------------------
        if "share" in ACTIONS:
            run_step(
                "Share",
                lambda: share_post(device_id),
                device_id
            )
            time.sleep(1)

        # -------------------------
        # 1️⃣2️⃣ Repost
        # -------------------------
        if "repost" in ACTIONS:
            run_step(
                "Repost",
                lambda: repost_post(device_id),
                device_id
            )
            time.sleep(1)

        # -------------------------
        # 🔁 Switch Account
        # -------------------------
        if "switch" in ACTIONS:
            run_step(
                "Switch Account",
                lambda: switch_account(device_id),
                device_id
            )

        debug_log(device_id, "🎯 Debug Worker Completed")

    except Exception as e:
        debug_log(device_id, f"🔥 CRASH → {e}")


# =========================
# RUN ALL DEVICES
# =========================
def run_debug_all_devices(device_ids):
    threads = []

    for device_id in device_ids:
        t = threading.Thread(
            target=debug_device,
            args=(device_id,),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    from engine.logic.device_auth import get_connected_adb_devices

    devices = get_connected_adb_devices()

    if not devices:
        print("❌ No devices connected")
    else:
        print(f"✅ Devices: {devices}")
        run_debug_all_devices(devices)