import time
import random
from engine.ui.reel_comment_loop import reel_comment_loop

def worker_reel(device_id):
    print(f"[{device_id}] 🎬 Reel Worker Started")

    try:
        # -------------------------
        # 2️⃣ Main Loop
        # -------------------------
        while True:
            print(f"[{device_id}] 🔁 Starting reel cycle")

            # run loop
            reel_comment_loop(
                device_id,
                total_reels=random.randint(10, 25)
            )

            # cooldown between cycles
            cooldown = random.randint(10, 60)
            print(f"[{device_id}] 💤 Cooling down {cooldown}s")
            time.sleep(cooldown)

    except Exception as e:
        print(f"[{device_id}] ❌ Reel worker crashed: {e}")
