import time
import random
import subprocess
from engine.post_monitor.monitor import PostMonitor
usernames = [
    "aesthetic.viren",
    "bholenath_jatt1811",
    "bite.me.up",
    "boonne.fashions",
    "bridesbyaashna",
    "choreographer_akash",
    "djdynameets",
    "eternalbright.in",
    "faizaansofficial",
    "friendsandcompany_official",
    "ftpix.in",
    "gauravkotharii",
    "hairtrendssalonsindia",
    "ifbbprojyotigupta",
    "laa_belle_salon",
    "lipika_maheshwari",
    "nightwalkerstheband",
    "onymedindia",
    "our_tiny_chapters",
    "ria_fashionblogger",
    "rjproductions_official",
    "shivanisharmafoundation",
    "swarnapraveen1",
    "tanmaynagpal_",
    "techbyrawat",
    "torqos.ev",
    "treasure_of_kutch",
    "vanitas_payal_beauty999",
    "vickygetfit",
    "vinayakoli",
    "wander_bites_duo",
    "wearstrangers"
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
