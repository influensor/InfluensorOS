import time
import random
import subprocess
from engine.post_monitor.monitor_new import PostMonitor
usernames = [
    "_immanzar_",
    "aesthetic.viren",
    "angelsmakeover.2005",
    "anshusworld",
    "aradhanasometimes",
    "arvindyadav",
    "bholenath_jatt1811",
    "brijeshpatelfotographi",
    "choreographer_akash",
    "diyasingh_dynameets",
    "dr_divyaprakashgavel",
    "eternalbright.in",
    "farzeencouture",
    "gauravkotharii",
    "hrishitaachopra",
    "hussainraniwala_",
    "iam.pushpindersingh",
    "ifbbprojyotigupta",
    "lipika_maheshwari",
    "ls_beautysalon_and_makeover",
    "makeupbyaashnaguglani",
    "nasuschauhan",
    "syed_swaleh",
    "tanmaynagpal_",
    "thedevpurush",
    "wander_bites_duo",
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

time.sleep(random.uniform(1, 30))

# =========================================
# AI COMMENT GENERATION
# =========================================
try:
    print("\n[AI] Starting ""comment generation...")
    subprocess.run(["python","ai_comments.py"])
except Exception as e:
    print(f"[AI] generator failed: {e}")
