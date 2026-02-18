from engine.post_monitor.monitor import PostMonitor
usernames = [
    "a4agharkar.in",
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

