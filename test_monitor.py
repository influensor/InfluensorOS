import time
import random
from engine.post_monitor.monitor import PostMonitor
usernames = [
    "_immanzar_",
    "diyasingh_dynameets",
    "eternalbright.in",
    "aanmolsharma__",
    "thedevpurush",
]

monitor = PostMonitor(headless=True)
results = monitor.check_multiple(usernames, limit=6)
monitor.close()
for username, posts in results.items():
    if posts:
        print(f"New posts for {username}:")
        for post in posts:
            print(post)
    else:
        print(f"No new posts for {username}")

time.sleep(random.uniform(10, 60))
