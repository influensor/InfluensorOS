import time
import random
from engine.post_monitor.monitor_new import PostMonitor
usernames = [
    #"a4agharkar.in",
    "_immanzar_",
    "angelsmakeover.2005",
    "arvindyadav",
    "bholenath_jatt1811",
    "diyasingh_dynameets",
    "eternalbright.in",
    "gauravkotharii",
    "iam.pushpindersingh",
    "ls_beautysalon_and_makeover",
    "makeupbyaashnaguglani",
    "syed_swaleh",
    "tanmaynagpal_",
    "thedevpurush",
]

monitor = PostMonitor(headless=True)
results = monitor.check_multiple(usernames, limit=8)
monitor.close()
for username, posts in results.items():
    if posts:
        print(f"New posts for {username}:")
        for post in posts:
            print(post)
    else:
        print(f"No new posts for {username}")

time.sleep(random.uniform(10, 60))
