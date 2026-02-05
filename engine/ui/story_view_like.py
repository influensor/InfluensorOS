import time, random, uiautomator2 as u2

STORY_VIEW_MIN = 1
STORY_VIEW_MAX = 3
MAX_STORIES = 10
LIKE_PROBABILITY = 0.75

def story_view_like(device_id):
    d = u2.connect(device_id)

    try:
        avatar = d(resourceId="com.instagram.android:id/reel_ring")
        if not avatar.exists(timeout=3):
            print(f"[{device_id}] story_view_like → avatar not found")
            return False

        avatar.click()
        time.sleep(2)

        stories_viewed = 0
        w, h = d.window_size()

        while stories_viewed < MAX_STORIES:

            like_btn = d(resourceId="com.instagram.android:id/toolbar_like_button")

            # 🚪 Exit if story ended
            if not like_btn.exists(timeout=0.5):
                break

            view_time = random.randint(STORY_VIEW_MIN, STORY_VIEW_MAX)
            time.sleep(view_time)

            if random.random() < LIKE_PROBABILITY:
                like_btn.click()
                print(f"[{device_id}] Story View Like → Liked Story")
                time.sleep(0.1)

            d.click(int(w * 0.99), int(h * 0.25))
            time.sleep(0.5)

            stories_viewed += 1

        d.press("back")
        time.sleep(1)
        print(f"[{device_id}] Story View Like → Done")
        return True

    except Exception as e:
        print(f"[{device_id}] Story View Like ERROR: {e}")
        try:
            d.press("back")
        except Exception:
            pass
        return False
