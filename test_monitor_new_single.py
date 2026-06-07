import os
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
    "faizaansofficial",
    "farzeencouture",
    "gauravkotharii",
    "hrishitaachopra",
    "hussainraniwala_",
    "iam.pushpindersingh",
    "ifbbprojyotigupta",
    "lipika_maheshwari",
    "ls_beautysalon_and_makeover",
    "makeupbyaashnaguglani",
    "muskankorea",
    "nasuschauhan",
    "shivanisharma_officia",
    "syed_swaleh",
    "tanmaynagpal_",
    "techboxervlogs",
    "wander_bites_duo",
 ]

INDEX_FILE = r"C:\Users\yagha\OneDrive\Documents\GitHub\InfluensorOS\current_user.txt"

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

monitor = PostMonitor(headless=True)
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