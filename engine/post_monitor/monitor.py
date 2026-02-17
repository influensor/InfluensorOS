from playwright.sync_api import sync_playwright
from .storage import load_saved_posts, save_posts
import time
import random

USER_DATA_DIR = r"C:\Users\yagha\OneDrive\Desktop\insta_profile"


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

    def fetch_posts(self, username, limit=10):
        self.page.goto(
            f"https://www.instagram.com/{username}/",
            wait_until="domcontentloaded"
        )

        self.page.wait_for_timeout(4000)
        self.page.mouse.wheel(0, 1500)
        self.page.wait_for_timeout(2000)

        posts = self.page.locator("a[href*='/p/'], a[href*='/reel/']")
        count = posts.count()

        links = []
        for i in range(count):
            href = posts.nth(i).get_attribute("href")
            if href:
                full_url = "https://www.instagram.com" + href
                if full_url not in links:
                    links.append(full_url)

        return links[:limit]

    def check_user(self, username, limit=10):
        latest_posts = self.fetch_posts(username, limit)
        saved_posts = load_saved_posts(username)

        new_posts = [p for p in latest_posts if p not in saved_posts]

        if new_posts:
            updated = new_posts + saved_posts
            save_posts(username, updated)

        return new_posts

    def check_multiple(self, usernames, limit=10):
        results = {}

        for username in usernames:
            try:
                new_posts = self.check_user(username, limit)
                results[username] = new_posts
            except Exception as e:
                print(f"Error processing {username}: {e}")
                results[username] = []

            time.sleep(random.uniform(2, 5))

        return results
