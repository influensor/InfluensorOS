import time
import random
import subprocess
from engine.post_monitor.monitor import PostMonitor
usernames = [
    "aanmolsharma__",
    "adityasatpute01",
    "aesthetic.viren",
    "anshusworld",
    "bholenath_jatt1811",
    "bite.me.up",
    "boonne.fashions",
    "bridesbyaashna",
    "choreographer_akash",
    "djdynameets",
    "eternalbright.in",
    "faizaansofficial",
    "friendsandcompany_official",
    "hairtrendssalonsindia",
    "ifbbprojyotigupta",
    "lipika_maheshwari",
    "ls_beautysalon_and_makeover",
    "muskankorea",
    "nasuschauhan",
    "novaraa_internationals__",
    "our_tiny_chapters",
    "pragyas353",
    "prateekbabarfitness",
    "swarnapraveen1",
    "syed_swaleh",
    "tanmaynagpal_",
    "techbyrawat",
    "vanitas_payal_beauty999",
    "vickygetfit",
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
