import os
import json
from playwright.sync_api import sync_playwright


# =====================================================
# CONFIG
# =====================================================

USER_DATA_DIR = (
    r"C:\instagram_a4agharkar.in"
)

BASE_DIR = os.path.join(
    os.path.dirname(__file__),
    "data"
)

POSTS_DIR = os.path.join(
    BASE_DIR,
    "postsall"
)

os.makedirs(
    POSTS_DIR,
    exist_ok=True
)


# =====================================================
# SHORTCODE
# =====================================================

def extract_shortcode(url):

    try:

        parts = (
            url
            .strip("/")
            .split("/")
        )

        return parts[-1]

    except:
        return None


# =====================================================
# SAVE POSTS
# =====================================================

def save_posts(
    username,
    posts
):

    path = os.path.join(
        POSTS_DIR,
        f"{username}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            posts,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"[SAVED] "
        f"{len(posts)} posts"
    )


# =====================================================
# GET ALL POSTS
# =====================================================

def get_latest_posts(
    username,
    limit=100
):

    with sync_playwright() as p:

        context = (
            p.chromium
            .launch_persistent_context(
                USER_DATA_DIR,
                headless=True
            )
        )

        page = context.new_page()

        page.goto(
            f"https://www.instagram.com/{username}/",
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(5000)

        collected_posts = []

        seen = set()

        same_count_streak = 0
        last_count = 0

        # =========================================
        # SCROLL UNTIL LIMIT
        # =========================================

        while len(collected_posts) < limit:

            posts = page.locator(
                "a[href*='/p/'], a[href*='/reel/']"
            )

            count = posts.count()

            for i in range(count):

                try:

                    href = posts.nth(i).get_attribute(
                        "href"
                    )

                    if not href:
                        continue

                    full_url = (
                        "https://www.instagram.com"
                        + href
                    )

                    shortcode = extract_shortcode(
                        full_url
                    )

                    if not shortcode:
                        continue

                    if shortcode in seen:
                        continue

                    seen.add(shortcode)

                    normalized_url = (
                        "https://www.instagram.com/reel/"
                        f"{shortcode}/"
                    )

                    collected_posts.append({

                        "shortcode": shortcode,

                        "url": normalized_url,

                        "caption": "",

                        "ai_comments_generated": False
                    })

                except Exception:
                    continue

            print(
                f"Collected: "
                f"{len(collected_posts)}"
            )

            # =====================================
            # STOP IF NO NEW POSTS
            # =====================================

            if len(collected_posts) == last_count:

                same_count_streak += 1

                print(
                    f"No new posts... "
                    f"streak: "
                    f"{same_count_streak}"
                )

            else:

                same_count_streak = 0

            if same_count_streak >= 5:

                print(
                    "Stopping: "
                    "No more new posts loading"
                )

                break

            last_count = len(collected_posts)

            # =====================================
            # SCROLL
            # =====================================

            page.evaluate(
                "window.scrollTo("
                "0, document.body.scrollHeight)"
            )

            page.wait_for_timeout(5000)

        context.close()

        return collected_posts[:limit]


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    username = "faizaansofficial"
    posts = get_latest_posts(
        username,
        limit=16
    )
    save_posts(
        username,
        posts
    )
    print(
        f"\nDONE: "
        f"{len(posts)} posts saved"
    )
