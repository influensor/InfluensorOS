from playwright.sync_api import sync_playwright
from .storage import load_saved_posts, save_posts
import time
import random

USER_DATA_DIR = r"C:\Users\003\Desktop\insta_profile"


class PostMonitor:

    def __init__(self, headless=True):
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=headless
        )
        self.page = self.context.new_page()

    def close(self):
        self.context.close()
        self.playwright.stop()

    def extract_shortcode(self, href):
        """
        Extract shortcode from:
        /username/p/ABC123/
        /username/reel/ABC123/
        """
        parts = href.strip("/").split("/")
        return parts[-1] if parts else None

    def build_reel_path(self, shortcode):
        return f"https://www.instagram.com/reel/{shortcode}/"

    def fetch_reel_paths(self, username, limit=10):
        self.page.goto(
            f"https://www.instagram.com/{username}/",
            wait_until="domcontentloaded"
        )

        self.page.wait_for_timeout(4000)
        self.page.mouse.wheel(0, 1500)
        self.page.wait_for_timeout(2000)

        posts = self.page.locator("a[href*='/p/'], a[href*='/reel/']")
        count = posts.count()

        reel_paths = []

        for i in range(count):
            href = posts.nth(i).get_attribute("href")
            if href:
                shortcode = self.extract_shortcode(href)
                if shortcode:
                    reel_path = self.build_reel_path(shortcode)

                    if reel_path not in reel_paths:
                        reel_paths.append(reel_path)

        return reel_paths[:limit]

    def check_user(self, username, limit=10):
        latest_reels = self.fetch_reel_paths(username, limit)
        saved_reels = load_saved_posts(username)

        new_reels = [r for r in latest_reels if r not in saved_reels]

        if new_reels:
            updated = new_reels + saved_reels
            save_posts(username, updated)

        return new_reels

    def check_multiple(self, usernames, limit=10):
        results = {}

        for username in usernames:
            try:
                new_reels = self.check_user(username, limit)
                results[username] = new_reels
            except Exception as e:
                print(f"Error processing {username}: {e}")
                results[username] = []

            time.sleep(random.uniform(2, 5))

        return results
