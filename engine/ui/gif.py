import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn, error


# =========================
# CONFIG
# =========================

GIF_KEYWORDS = [

    # 🔥 Hype / Fire
    "fire", "lit", "legend", "goat", "insane", "crazy",
    "epic", "unreal", "mad", "next level", "boom",
    "explosion", "wow", "omg", "shocked", "mind blown",

    # ❤️ Love / Cute
    "love", "heart", "kiss", "cute", "adorable",
    "aww", "sweet", "romantic", "hug", "blush",
    "baby", "cutie", "beautiful", "pretty", "gorgeous",

    # 😂 Funny / Laugh
    "lol", "haha", "funny", "laugh", "rofl",
    "lmao", "crying laughing", "dead", "hilarious",
    "comedy", "clown", "meme", "sarcasm", "awkward",

    # 👏 Appreciation
    "clap", "applause", "respect", "salute",
    "well done", "bravo", "proud", "amazing",
    "fantastic", "incredible", "nice", "cool",

    # 😎 Attitude / Savage
    "savage", "boss", "attitude", "flex",
    "mic drop", "period", "queen", "king",
    "slay", "iconic", "confidence", "swagger",

    # 🤯 Shock / Reaction
    "what", "seriously", "no way", "impressed",
    "speechless", "surprised", "stunned",
    "dramatic", "slow clap", "facepalm",

    # 💃 Celebration
    "party", "celebrate", "dance", "happy",
    "excited", "yay", "cheers", "victory",
    "win", "success", "congrats", "champion",

    # 😢 Emotional
    "cry", "emotional", "tears", "sad",
    "heartbreak", "feels", "deep", "mood",
    "relatable", "vibes", "energy",

    # 😍 Reaction Faces
    "shy", "wink", "smile", "grin",
    "eye roll", "side eye", "nervous",
    "thinking", "hmm", "huh",

    # 🧠 Smart / Genius
    "genius", "smart", "brain", "idea",
    "calculated", "strategy", "plan",
    "thinking hard", "plot twist",

    # 💯 Validation
    "facts", "true", "exactly", "accurate",
    "this", "approved", "certified",
    "100", "real talk", "on point",

    # 🎬 Pop Culture
    "marvel", "bollywood", "hollywood",
    "anime", "kpop", "celebrity",
    "movie reaction", "tv show",
    "friends tv", "office reaction",

    # 🤡 Fun Extras
    "vibing", "chill", "bro", "bruh",
    "girl power", "boy energy",
    "dramatic entrance", "slow motion",
    "dance move", "happy dance",

    # 💪 Motivation
    "motivation", "grind", "hustle",
    "focus", "determined", "strong",
    "power move", "level up",

    # 🧨 Trendy
    "trending", "viral", "mood",
    "aesthetic", "vibe check",
    "main character", "energy shift",

    # 🫡 Respect / Support
    "support", "loyal", "solid",
    "trust", "respectfully",
    "big respect", "legendary"
]

# =========================
# MAIN FUNCTION
# =========================

def post_gif_comment(device_id, retries=2):
    """
    Posts a random GIF comment on currently opened Instagram post/reel.

    Handles:
    - Normal GIF screen
    - Avatar sticker default tab issue
    - Resolution independence
    - Multi-device compatibility

    Returns True if successful, else False
    """

    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ GIF Comment (attempt {attempt})", device_id)

        try:
            # -------------------------
            # 1️⃣ Open comment sheet
            # -------------------------
            comment_btn = d(descriptionContains="Comment")

            if not comment_btn.exists(timeout=3):
                warn("Comment button not found", device_id)
                return False

            comment_btn.click()
            time.sleep(1.5)

            # -------------------------
            # 2️⃣ Open GIF picker
            # -------------------------
            gif_btn = d(
                resourceId="com.instagram.android:id/comment_composer_animated_image_picker_button"
            )

            if not gif_btn.exists(timeout=3):
                warn("GIF picker button not found", device_id)
                d.press("back")
                return False

            gif_btn.click()
            time.sleep(1.5)

            # -------------------------
            # 3️⃣ Handle Avatar Stickers Screen (Edge Case)
            # -------------------------
            avatar_title = d(
                resourceId="com.instagram.android:id/no_avatar_nux_title"
            )

            if avatar_title.exists(timeout=2):
                info("Avatar screen detected → switching to GIF tab", device_id)

                gif_tab = d(description="GIFs")

                if gif_tab.exists(timeout=3):
                    gif_tab.click()
                    time.sleep(1.2)
                else:
                    warn("GIF tab button not found", device_id)
                    d.press("back")
                    d.press("back")
                    return False

            # -------------------------
            # 4️⃣ Wait for Search GIPHY field
            # -------------------------
            search_box = d(
                resourceId="com.instagram.android:id/search_edit_text"
            )

            if not search_box.exists(timeout=5):
                warn("Search GIPHY box not found", device_id)
                d.press("back")
                d.press("back")
                return False

            search_box.click()
            time.sleep(0.5)

            # -------------------------
            # 5️⃣ Type random keyword
            # -------------------------
            keyword = random.choice(GIF_KEYWORDS)
            info(f"GIF keyword → {keyword}", device_id)

            d.clear_text()
            d.send_keys(keyword, clear=False)
            time.sleep(2)

            # -------------------------
            # 6️⃣ Wait for GIF results
            # -------------------------
            gif_buttons = d(
                className="android.widget.Button",
                resourceId="com.instagram.android:id/gif_image"
            )

            if not gif_buttons.exists(timeout=5):
                warn("GIF results not loaded", device_id)
                d.press("back")
                d.press("back")
                return False

            count = gif_buttons.count

            if count == 0:
                warn("GIF list empty", device_id)
                d.press("back")
                d.press("back")
                return False

            # -------------------------
            # Optional human-like scroll
            # -------------------------
            grid = d(resourceId="com.instagram.android:id/gifs_tray_grid")

            if grid.exists and random.random() < 0.4:
                grid.scroll.vert.forward(steps=10)
                time.sleep(1)
                count = gif_buttons.count

            if count == 0:
                warn("No GIFs after scroll", device_id)
                return False

            # -------------------------
            # 7️⃣ Click random GIF
            # -------------------------
            index = random.randint(0, count - 1)
            gif_buttons[index].click()
            time.sleep(1)

            # -------------------------
            # 8️⃣ Close comment sheet
            # -------------------------
            d.press("back")
            time.sleep(0.5)

            info("✅ GIF comment posted", device_id)
            return True

        except Exception as e:
            warn(f"GIF error: {e}", device_id)

            try:
                d.press("back")
            except Exception:
                pass

            time.sleep(1)

    error("❌ GIF comment failed after retries", device_id)
    return False