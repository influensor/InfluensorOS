import os
import time
import random
import subprocess
from engine.post_monitor.monitor_new import PostMonitor

usernames = [
    "farzeencouture",
 ]

#INDEX_FILE = r"C:\Users\yagha\OneDrive\Documents\GitHub\InfluensorOS\current_user.txt"
INDEX_FILE = r"C:\Users\003\Documents\GitHub\InfluensorOS\current_user.txt"

# =========================================
# LOAD LAST INDEX
# =========================================
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, "r") as f:
        current_index = int(f.read().strip())
else:
    current_index = 0

# =========================================
# PICK ONLY ONE USER
# =========================================
username = usernames[current_index]

print(f"Processing: {username}")

monitor = PostMonitor(headless=False)
results = monitor.check_multiple([username], limit=12)
monitor.close()

for username, posts in results.items():
    if posts:
        print(f"New posts for {username}:")
        for post in posts:
            print(post)
    else:
        print(f"No new posts for {username}")

# =========================================
# SAVE NEXT USER INDEX
# =========================================
next_index = (current_index + 1) % len(usernames)

with open(INDEX_FILE, "w") as f:
    f.write(str(next_index))

time.sleep(random.uniform(1, 30))

# =========================================
# AI COMMENT GENERATION
# =========================================
try:
    print("\n[AI] Starting comment generation...")
    subprocess.run(["python", "ai_comments.py"])
except Exception as e:
    print(f"[AI] generator failed: {e}")