import time
import threading
import subprocess

from engine.worker import device_worker
from engine.logic.device_auth import (
    get_connected_adb_devices,
    load_allowed_devices,
    filter_authorized
)
from engine.logic.kill_switch import enabled as kill_switch_enabled


# =========================
# BOOTSTRAP CONFIG
# =========================
BOOTSTRAP_REFRESH_SECONDS = 10


def start_device_worker(device_id):
    """
    Wrapper to isolate worker crashes per device
    """
    try:
        device_worker(device_id)
    except Exception as e:
        print(f"[BOOTSTRAP] Worker crashed on {device_id}: {e}")


def bootstrap_loop():
    print("[BOOTSTRAP] InfluensorOS starting...")

    while True:
        # -------------------------
        # Global kill switch
        # -------------------------
        if not kill_switch_enabled():
            print("[BOOTSTRAP] Kill switch OFF. Sleeping...")
            time.sleep(BOOTSTRAP_REFRESH_SECONDS)
            continue

        # -------------------------
        # Detect connected devices
        # -------------------------
        connected = get_connected_adb_devices()
        if not connected:
            print("[BOOTSTRAP] No ADB devices connected")
            time.sleep(BOOTSTRAP_REFRESH_SECONDS)
            continue

        # -------------------------
        # Filter allowed devices
        # -------------------------
        allowed_config = load_allowed_devices()
        allowed_devices = filter_authorized(connected, allowed_config)

        if not allowed_devices:
            print("[BOOTSTRAP] No authorized devices")
            time.sleep(BOOTSTRAP_REFRESH_SECONDS)
            continue

        print(f"[BOOTSTRAP] Authorized devices: {allowed_devices}")

        # -------------------------
        # Spawn workers (one per device)
        # -------------------------
        threads = []

        for device_id in allowed_devices:
            t = threading.Thread(
                target=start_device_worker,
                args=(device_id,),
                daemon=True
            )
            t.start()
            threads.append(t)

        # -------------------------
        # Wait for all workers
        # -------------------------
        for t in threads:
            t.join()

        # -------------------------
        # Cooldown before next cycle
        # -------------------------
        print("[BOOTSTRAP] All device cycles complete. Cooling down...")
        time.sleep(BOOTSTRAP_REFRESH_SECONDS)


# =========================
# ENTRY POINT
# =========================
def start():
    bootstrap_loop()
