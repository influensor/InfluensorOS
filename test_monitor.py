import time
import random
import subprocess
from engine.post_monitor.monitor import PostMonitor
usernames = [
    "_thecosmicvoid",
    "aesthetic.viren",
    "ananya_raoo",
    "bite.me.up",
    "bridesbyaashna",
    "choreographer_akash",
    "djdynameets",
    "eternalbright.in",
    "faizaansofficial",
    "fit__yatra",
    "friendsandcompany_official",
    "houseofstylebyricha",
    "immaculatelimoinc",
    "journey.techie",
    "laa_belle_salon",
    "ria_fashionblogger",
    "shivanisharma_officia",
    "theumangblog",
    "torqos.ev",
    "treasure_of_kutch",
    "trishachatterjee09",
    "vanitas_payal_beauty999",
    "vickygetfit",
    "wander_bites_duo",
    "wearstrangers",
    "worldspassport"
 ]

monitor = PostMonitor(headless=True)
results = monitor.check_multiple(usernames, limit=12)
monitor.close()
for username, posts in results.items():
    if posts:
        print(f"New posts for {username}:")
        for post in posts:
            print(post)
    else:
        print(f"No new posts for {username}")

time.sleep(random.uniform(1, 10))

# =========================================
# AI COMMENT GENERATION
# =========================================
try:
    print("\n[AI] Starting ""comment generation...")
    subprocess.run(["python","ai_comments.py"])
except Exception as e:
    print(f"[AI] generator failed: {e}")
