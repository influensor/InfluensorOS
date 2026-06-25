import time
import random
import subprocess
from engine.post_monitor.monitor_new import PostMonitor
usernames = [
    "aiadventureworld",
    "angelsmakeover.2005",
    "anshusworld",
    "aradhanasometimes",
    "arvindyadav",
    "ashok__chaudhary___",
    "bholenath_jatt1811",
    "bite.me.up",
    "choreographer_akash",
    "dannydaanishofficial",
    "digibuiltsolutions",
    "djdynameets",
    "dr_divyaprakashgavel",
    "eternalbright.in",
    "faizaansofficial",
    "farzeencouture",
    "hrishitaachopra",
    "lipika_maheshwari",
    "ls_beautysalon_and_makeover",
    "makeupbyaashnaguglani",
    "muskankorea",
    "swarnapraveen1",
    "syed_swaleh",
    "tanmaynagpal_",
    "techboxervlogs",
    "techbyrawat",
    "the_movie_craft",
    "veekshadiaries",
    "vickygetfit",
 ]

monitor = PostMonitor(headless=False)
results = monitor.check_multiple(usernames, limit=12)
monitor.close()
for username, posts in results.items():
    if posts:
        print(f"New posts for {username}:")
        for post in posts:
            print(post)
    else:
        print(f"No new posts for {username}")

time.sleep(random.uniform(1, 30))

# =========================================
# AI COMMENT GENERATION
# =========================================
try:
    print("\n[AI] Starting ""comment generation...")
    subprocess.run(["python","ai_comments.py"])
except Exception as e:
    print(f"[AI] generator failed: {e}")
