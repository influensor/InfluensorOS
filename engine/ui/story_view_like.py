import time
import random
import uiautomator2 as u2

INSTAGRAM_PKG = "com.instagram.android"

STORY_VIEW_MIN = 1
STORY_VIEW_MAX = 10
MAX_STORIES = 10
LIKE_PROBABILITY = 0.5  # 50%


def story_view_like(device_id):
    """
    - Detects if profile has story
    - Opens story
    - Views 1–3 stories
    - Randomly likes story
    - Safely exits back to profile
    """

    d = u2.connect(device_id)

    try:
        # 🔍 Story ring on profile picture
        story_ring = d(
            resourceId="com.instagram.android:id/profile_header_avatar"
        )

        if not story_ring.exists(timeout=3):
            return False

        # 🟣 Story exists → open
        story_ring.click()
        time.sleep(1)

        stories_viewed = 0

        while stories_viewed < MAX_STORIES:
            view_time = random.randint(STORY_VIEW_MIN, STORY_VIEW_MAX)
            time.sleep(view_time)

            # ❤️ Random like
            if random.random() < LIKE_PROBABILITY:
                if d(description="Like").exists(timeout=0.5):
                    d(description="Like").click()
                    time.sleep(0.5)

            stories_viewed += 1

            # ➡️ Next story
            if d(description="Next").exists(timeout=0.5):
                d(description="Next").click()
                time.sleep(0.5)
            else:
                break

        # ⬅️ Exit story safely
        d.press("back")
        time.sleep(1)

        return True

    except Exception as e:
        print(f"[{device_id}] Story view error: {e}")
        try:
            d.press("back")
        except Exception:
            pass
        return False
