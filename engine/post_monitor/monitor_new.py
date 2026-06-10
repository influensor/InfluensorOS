import os
import re
import time
import random
import json

from playwright.sync_api import sync_playwright
from .storage_new import load_saved_posts, save_posts


# =====================================================
# CONFIG
# =====================================================

PROFILES = [
#    r"C:\Users\003\AppData\Local\Google\Chrome\User Data\Default",
    r"C:\Users\003\AppData\Local\Google\Chrome\User Data\Profile 2",
]
USER_DATA_DIR = random.choice(PROFILES)
POST_COUNT_FILE = r"C:\Users\003\Documents\GitHub\InfluensorOS\data\post_counts.json"


class PostMonitor:
    def __init__(self, headless=True):
        self.playwright = sync_playwright().start()
        self.context = (
            self.playwright.chromium
            .launch_persistent_context(
                USER_DATA_DIR,
                headless=headless
            )
        )
        self.page = self.context.new_page()


    # =====================================================
    # POST COUNT STORAGE
    # =====================================================

    def load_post_counts(self):

        if not os.path.exists(
            POST_COUNT_FILE
        ):
            return {}

        try:

            with open(
                POST_COUNT_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except:

            return {}


    def save_post_counts(
        self,
        counts
    ):

        with open(
            POST_COUNT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                counts,
                f,
                indent=2
            )


    # =====================================================
    # GET PROFILE POST COUNT
    # =====================================================

    def get_post_count(
        self,
        username
    ):

        try:

            self.page.goto(
                f"https://www.instagram.com/{username}/",
                wait_until="domcontentloaded"
            )

            self.page.wait_for_timeout(
                3000
            )

            html = self.page.content()

            match = re.search(
                r'(\d+(?:,\d+)*)\s+Posts',
                html,
                re.IGNORECASE
            )

            if match:

                return int(
                    match.group(1)
                    .replace(",", "")
                )

        except Exception as e:

            print(
                f"[COUNT ERROR] "
                f"{username}: {e}"
            )

        return None
    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.context.close()
        self.playwright.stop()

    # =====================================================
    # SHORTCODE
    # =====================================================

    def extract_shortcode(self, href):

        try:

            parts = (
                href
                .strip("/")
                .split("/")
            )

            return parts[-1]

        except:
            return None

    # =====================================================
    # BUILD POST URL
    # =====================================================

    def build_post_url(self, href):

        return (
            "https://www.instagram.com"
            + href
        )

    # =====================================================
    # BUILD NORMALIZED URL
    # =====================================================

    def build_normalized_url(
        self,
        shortcode
    ):

        return (
            "https://www.instagram.com/reel/"
            f"{shortcode}/"
        )

    # =====================================================
    # CLEAN TEXT
    # =====================================================

    def clean_text(self, text):

        if not text:
            return ""

        try:

            text = bytes(
                text,
                "utf-8"
            ).decode(
                "unicode_escape"
            )

        except Exception:
            pass

        text = text.replace(
            "\\n",
            " "
        )

        text = text.replace(
            '\\"',
            '"'
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        text = text.encode(
            "utf-8",
            "ignore"
        ).decode(
            "utf-8",
            "ignore"
        )

        return text

    # =====================================================
    # EXTRACT CAPTION
    # =====================================================

    def extract_caption(
        self,
        html
    ):

        try:

            patterns = [
                r'"caption":\{.*?"text":"((?:\\.|[^"])*)"',
                r'"caption":\{[^}]*"text":"((?:\\.|[^"])*)"'
                #r'"caption":\{.*?"text":"(.*?)"',
                #r'"caption":\{[^}]*"text":"(.*?)"',
                #r'"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"(.*?)"\}\}\]',
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    html,
                    re.DOTALL
                )

                if not match:
                    continue

                text = self.clean_text(
                    match.group(1)
                )

                text = text.split(
                    '","'
                )[0]

                if len(text) < 5:
                    continue

                return text

        except Exception as e:

            print(
                f"[caption error] {e}"
            )

        return ""

    # =====================================================
    # FETCH PROFILE POST LIST
    # =====================================================

    def fetch_post_list(
        self,
        username,
        limit=100
    ):

        self.page.goto(
            f"https://www.instagram.com/{username}/",
            wait_until="domcontentloaded"
        )

        self.page.wait_for_timeout(30000)

        collected_posts = []

        seen = set()

        same_count_streak = 0
        last_count = 0

        # =========================================
        # SCROLL UNTIL LIMIT
        # =========================================

        while len(collected_posts) < limit:

            posts = self.page.locator(
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

                    shortcode = self.extract_shortcode(
                        href
                    )

                    if not shortcode:
                        continue

                    if shortcode in seen:
                        continue

                    seen.add(shortcode)

                    collected_posts.append({

                        "shortcode": shortcode,

                        "url": self.build_post_url(
                            href
                        )
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

            self.page.evaluate(
                "window.scrollTo("
                "0, document.body.scrollHeight)"
            )

            self.page.wait_for_timeout(2000)

        return collected_posts[:limit]

    # =====================================================
    # FETCH SINGLE POST DATA
    # =====================================================
    def build_p_url(self, shortcode):
        return f"https://www.instagram.com/p/{shortcode}/"

    def fetch_post_data(
        self,
        shortcode,
        post_url
    ):

        try:

            # -------------------------------------
            # ISOLATED PAGE
            # -------------------------------------

            post_page = self.context.new_page()

            p_url = self.build_p_url(shortcode)
            print(f"[OPENING] {p_url}")
            
            post_page.goto(
                p_url,
                wait_until="domcontentloaded"
            )

            post_page.wait_for_load_state(
                "networkidle"
            )

            post_page.wait_for_timeout(
                random.randint(3000, 5000)
            )

            html = post_page.content()

            caption = self.extract_caption(
                html
            )

            post_page.close()

            normalized_url = (
                self.build_normalized_url(
                    shortcode
                )
            )

            return {

                "shortcode": shortcode,

                "url": normalized_url,

                "caption": caption,

                "ai_comments_generated": False
            }

        except Exception as e:

            print(
                f"[monitor] failed "
                f"{post_url}: {e}"
            )

        return None

    # =====================================================
    # CHECK USER
    # =====================================================

    def check_user(
        self,
        username,
        limit=100
    ):

        # -----------------------------------------
        # LOAD SAVED POSTS
        # -----------------------------------------

        saved_posts = load_saved_posts(
            username
        )

        saved_shortcodes = {

            p.get("shortcode")

            for p in saved_posts
        }

        # -----------------------------------------
        # FETCH PROFILE POSTS
        # -----------------------------------------

        latest_post_list = self.fetch_post_list(
            username,
            limit
        )

        # -----------------------------------------
        # FIND NEW POSTS
        # -----------------------------------------

        new_post_list = [

            p for p in latest_post_list

            if p["shortcode"]
            not in saved_shortcodes
        ]

        # -----------------------------------------
        # FETCH ONLY NEW POST DATA
        # -----------------------------------------

        new_posts = []

        for post in new_post_list:

            data = self.fetch_post_data(

                post["shortcode"],

                post["url"]
            )

            if data:

                new_posts.append(data)

                print(
                    f"[POST] "
                    f"{username} → "
                    f"{data['shortcode']}"
                )

        # -----------------------------------------
        # BUILD ORDERED STRUCTURE
        # -----------------------------------------

        ordered_posts = []

        seen = set()

        # -----------------------------------------
        # 1. CURRENT PROFILE ORDER
        # -----------------------------------------

        for live_post in latest_post_list:

            shortcode = live_post["shortcode"]

            # existing saved
            existing = next(

                (
                    p for p in saved_posts

                    if p.get("shortcode")
                    == shortcode
                ),

                None
            )

            if existing:

                ordered_posts.append(
                    existing
                )

                seen.add(shortcode)

                continue

            # new fetched
            generated = next(

                (
                    p for p in new_posts

                    if p.get("shortcode")
                    == shortcode
                ),

                None
            )

            if generated:

                ordered_posts.append(
                    generated
                )

                seen.add(shortcode)

        # -----------------------------------------
        # 2. APPEND HISTORICAL POSTS
        # -----------------------------------------

        for old_post in saved_posts:

            shortcode = old_post.get(
                "shortcode"
            )

            if shortcode in seen:
                continue

            ordered_posts.append(
                old_post
            )

        # -----------------------------------------
        # SAVE
        # -----------------------------------------

        save_posts(
            username,
            ordered_posts
        )

        return new_posts

    # =====================================================
    # CHECK MULTIPLE USERS
    # =====================================================

    def check_multiple(
        self,
        usernames,
        limit=100
    ):
    
        results = {}
    
        counts = self.load_post_counts()
    
        changed_users = []
    
        # =========================================
        # FAST PROFILE CHECK
        # =========================================
    
        for username in usernames:
    
            try:
    
                current_count = (
                    self.get_post_count(
                        username
                    )
                )
    
                if current_count is None:
                    continue
    
                old_count = counts.get(
                    username,
                    0
                )
    
                print(
                    f"[COUNT] "
                    f"{username}: "
                    f"{old_count} -> "
                    f"{current_count}"
                )
    
                if current_count > old_count:
    
                    changed_users.append(
                        username
                    )
    
                    counts[
                        username
                    ] = current_count
    
            except Exception as e:
    
                print(
                    f"[COUNT ERROR] "
                    f"{username}: {e}"
                )
    
        self.save_post_counts(
            counts
        )
    
        print(
            f"\nUsers With New Posts: "
            f"{len(changed_users)}"
        )
    
        # =========================================
        # EXISTING LOGIC
        # =========================================
    
        for username in changed_users:
    
            try:
    
                print(
                    f"\n[CHECKING] "
                    f"{username}"
                )
    
                posts = self.check_user(
                    username,
                    limit
                )
    
                results[
                    username
                ] = posts
    
                print(
                    f"[DONE] "
                    f"{username} → "
                    f"{len(posts)} new posts"
                )
    
            except Exception as e:
    
                print(
                    f"[ERROR] processing "
                    f"{username}: {e}"
                )
    
                results[
                    username
                ] = []
    
            time.sleep(
                random.uniform(
                    1,
                    5
                )
            )
    
        return results