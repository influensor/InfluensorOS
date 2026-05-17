import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn, error


# =========================
# CONFIG
# =========================
STORY_VIEW_MIN = 1
STORY_VIEW_MAX = 1

MAX_STORIES = 15
LIKE_PROBABILITY = 0.50


# =========================
# PROFILE SELECTORS
# =========================
STORY_OPEN_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/row_profile_header_imageview_frame_layout"
    },
]


# =========================
# STORY VIEWER SELECTORS
# =========================
STORY_VIEWER_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/reel_viewer_root"
    }
]


# =========================
# STORY LIKE SELECTORS
# =========================
STORY_LIKE_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/toolbar_like_button"
    },
    {
        "descriptionContains":
        "Like Story"
    },
]


# =========================
# HELPERS
# =========================
def _find_ui(d, selectors, timeout=1):

    for sel in selectors:

        ui = d(**sel)

        try:
            if ui.exists(timeout=timeout):
                return ui
        except Exception:
            pass

    return None


def _is_story_viewer_open(d):

    return d(
        resourceId="com.instagram.android:id/reel_viewer_root"
    ).exists(timeout=1)


def _has_unseen_story(d):

    avatar = d(
        resourceId=
        "com.instagram.android:id/row_profile_header_imageview"
    )

    if not avatar.exists(timeout=2):
        return False

    try:

        desc = (
            avatar.info.get("contentDescription", "")
            .lower()
            .strip()
        )

        return (
            "unseen story" in desc
            or "new story" in desc
            or "0 of 0, Seen." in desc
        )

    except Exception:
        return False


# =========================
# STORY VIEW + LIKE
# =========================
def story_view_like(device_id, retries=1):

    d = get_device(device_id)

    for attempt in range(1, retries + 1):

        info(
            f"▶ Story View Like (attempt {attempt})",
            device_id
        )

        try:

            # =====================================
            # 1️⃣ CHECK UNSEEN STORY
            # =====================================
            if not _has_unseen_story(d):

                info(
                    "⚠ No Unseen Story Available",
                    device_id
                )

                return True

            # =====================================
            # 2️⃣ FIND STORY BUTTON
            # =====================================
            story_btn = _find_ui(
                d,
                STORY_OPEN_SELECTORS,
                timeout=3
            )

            if not story_btn:

                warn(
                    "⚠ Story Button Not Found",
                    device_id
                )

                return False

            # =====================================
            # 3️⃣ OPEN STORY
            # =====================================
            story_btn.click()

            time.sleep(
                random.uniform(1, 3)
            )

            # =====================================
            # 4️⃣ VERIFY STORY VIEWER OPENED
            # =====================================
            if not _is_story_viewer_open(d):

                warn(
                    "⚠ Story Viewer Failed To Open",
                    device_id
                )

                return False

            # =====================================
            # 5️⃣ VIEW STORIES LOOP
            # =====================================
            stories_viewed = 0

            w, h = d.window_size()

            while stories_viewed < MAX_STORIES:

                # ---------------------------------
                # EXIT IF VIEWER CLOSED
                # ---------------------------------
                if not _is_story_viewer_open(d):

                    info(
                        f"✅ Story Sequence Completed "
                        f"({stories_viewed} Stories)",
                        device_id
                    )

                    return True

                # ---------------------------------
                # HUMAN VIEW DELAY
                # ---------------------------------
                view_time = random.uniform(
                    STORY_VIEW_MIN,
                    STORY_VIEW_MAX
                )

                time.sleep(view_time)

                # ---------------------------------
                # FIND LIKE BUTTON
                # ---------------------------------
                like_btn = _find_ui(
                    d,
                    STORY_LIKE_SELECTORS,
                    timeout=0.5
                )

                # ---------------------------------
                # RANDOM LIKE
                # ---------------------------------
                if (
                    like_btn
                    and random.random() < LIKE_PROBABILITY
                ):

                    try:

                        info_obj = like_btn.info

                        desc = (
                            info_obj.get(
                                "contentDescription"
                            ) or ""
                        ).lower()

                        # Skip already liked
                        if "liked" in desc:

                            info(
                                "⚠ Story Already Liked → Skipping",
                                device_id
                            )

                        else:

                            like_btn.click()

                            info(
                                "❤️ Story Liked",
                                device_id
                            )

                            time.sleep(
                                random.uniform(0.1, 0.5)
                            )

                    except Exception as e:

                        warn(
                            f"⚠ Story Like Failed: {e}",
                            device_id
                        )

                # ---------------------------------
                # NEXT STORY
                # ---------------------------------
                try:

                    d.click(
                        int(w * 0.99),
                        int(h * 0.30)
                    )

                except Exception as e:

                    warn(
                        f"⚠ Next Story Tap Failed: {e}",
                        device_id
                    )

                time.sleep(
                    random.uniform(0.5, 1.5)
                )

                stories_viewed += 1

            # =====================================
            # SAFETY EXIT
            # =====================================
            info(
                f"✅ Story View Limit Reached "
                f"({stories_viewed} Stories)",
                device_id
            )

            try:
                d.press("back")
            except Exception:
                pass

            return True

        except Exception as e:

            warn(
                f"⚠ Story View Like Error: {e}",
                device_id
            )

            time.sleep(1)

    error(
        "❌ Story View Like Failed After Retries",
        device_id
    )

    return False