import os
import re
import time
import random
import json
import html
    
from playwright.sync_api import sync_playwright
from .storage_new import load_saved_posts, save_posts


# =====================================================
# CONFIG
# =====================================================

PROFILES = [
    r"C:\instagram_a4agharkar.in",
    r"C:\instagram_abhijit.agharkar",
    r"C:\instagram_blackaquaindia.in",
    r"C:\instagram_mimy_ai",
    r"C:\instagram_nashikonwheels",
    r"C:\instagram_shophudabeauty.in",
]
USER_DATA_DIR = random.choice(PROFILES)

POST_COUNT_FILE = r"C:\Users\003\Documents\GitHub\InfluensorOS\data\post_counts.json"
#POST_COUNT_FILE = r"C:\Users\yagha\OneDrive\Documents\GitHub\InfluensorOS\data\post_counts.json"

VIEWPORTS = [
    # HD
    {"width": 1366, "height": 768},
    {"width": 1360, "height": 768},
    {"width": 1280, "height": 720},
    # Common Laptop
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
    # Full HD
    {"width": 1920, "height": 1080},
    {"width": 1900, "height": 1040},
    {"width": 1910, "height": 1070},
    # Higher Resolution
    {"width": 1680, "height": 1050},
    {"width": 1728, "height": 1117},
    {"width": 1792, "height": 1120},
    # MacBook Air
    {"width": 1440, "height": 823},
    # MacBook Pro
    {"width": 1512, "height": 982},
    {"width": 1728, "height": 1117},
    {"width": 1800, "height": 1169},
    # QHD
    {"width": 2560, "height": 1440},
    {"width": 2560, "height": 1600},
    # Ultrawide
    {"width": 2560, "height": 1080},
    {"width": 3440, "height": 1440},
]


USER_AGENTS = [
    # =========================
    # Google Chrome - Windows
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    # Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    # =========================
    # Microsoft Edge - Windows
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
    # =========================
    # Firefox - Windows
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    # =========================
    # Brave - Windows
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # =========================
    # Opera - Windows
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 OPR/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 OPR/121.0.0.0",
    # =========================
    # Chrome Windows 10 x86
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # =========================
    # Firefox Windows x86
    # =========================
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:138.0) Gecko/20100101 Firefox/138.0",
    # =========================
    # Older Windows 10
    # =========================
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
]

class PostMonitor:
    def __init__(self, headless=True):
        self.playwright = sync_playwright().start()
        self.context = (
            self.playwright.chromium
            .launch_persistent_context(
                USER_DATA_DIR,
                channel="chrome",
                headless=headless,
                viewport=random.choice(VIEWPORTS),
                user_agent=random.choice(USER_AGENTS),
                locale=random.choice([
                    "en-US",
                ]),
                args=[
                    "--disable-blink-features=AutomationControlled"
                ]
            )
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        print(f"[PROFILE] {USER_DATA_DIR}")
        print(f"[LOCALE] {self.page.evaluate('navigator.language')}")
        
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
                5000
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
    
        text = html.unescape(text)
    
        text = text.replace(
            "\\n",
            "\n"
        )
    
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()
    
        return text


    # =====================================================
    # EXTRACT CAPTION
    # =====================================================

    def extract_caption(
        self,
        html
    ):
    
        try:
    
            match = re.search(
                r'<meta property="og:description" content="([^"]*)"',
                html,
                re.DOTALL
            )
    
            if not match:
                return ""
    
            content = match.group(1)
    
            content = (
                content
                .replace("&quot;", '"')
                .replace("&#x2026;", "...")
                .replace("&#039;", "'")
            )
    
            # ----------------------------------
            # Extract text inside quotes
            # ----------------------------------
    
            quote_match = re.search(
                r':\s*"(.+?)"\.?\s*$',
                content,
                re.DOTALL
            )
    
            if quote_match:
    
                caption = quote_match.group(1)
    
                return self.clean_text(
                    caption
                )
    
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

        self.page.wait_for_timeout(60000)

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
                random.randint(5000, 10000)
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
                    changed_users.append((username,current_count))

            except Exception as e:
    
                print(
                    f"[COUNT ERROR] "
                    f"{username}: {e}"
                )


        print(
            f"\nUsers With New Posts: "
            f"{len(changed_users)}"
        )
    
        # =========================================
        # EXISTING LOGIC
        # =========================================
    
        for username, current_count in changed_users:
    
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
                
                if len(posts) == 0:
                    print(
                        f"[SKIP COUNT UPDATE] "
                        f"{username} returned 0 posts"
                    )
                    results[username] = []
                    continue

                counts[username] = current_count
                self.save_post_counts(counts)

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