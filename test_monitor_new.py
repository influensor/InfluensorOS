import time
import random
import subprocess
from engine.post_monitor.monitor_new import PostMonitor
usernames = [
    "aanmolsharma__",
    "aesthetic.viren",
    "aiadventureworld",
    "anshusworld",
    "arvindyadav",
    "bholenath_jatt1811",
    "bite.me.up",
    "boonne.fashions",
    "bridesbyaashna",
    "choreographer_akash",
    "djdynameets",
    "dr_divyaprakashgavel",
    "eternalbright.in",
    "faizaansofficial",
    "friendsandcompany_official",
    "hairtrendssalonsindia",
    "ifbbprojyotigupta",
    "lipika_maheshwari",
    "ls_beautysalon_and_makeover",
    "novaraa_internationals__",
    "pragyas353",
    "swarnapraveen1",
    "syed_swaleh",
    "tanmaynagpal_",
    "techbyrawat",
    "vanitas_payal_beauty999",
    "veekshadiaries",
    "vickygetfit",
    "wander_bites_duo",
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
