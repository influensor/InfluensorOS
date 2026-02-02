import time
import threading

from engine.worker import device_worker
from engine.logic.device_auth import (
    get_connected_adb_devices,
    get_authorized_devices,
)
from engine.logic.remote_config import kill_switch_active

# =========================
# BOOTSTRAP CONFIG
# =========================
BOOTSTRAP_REFRESH_SECONDS = 10


def start_device_worker(device_id):
    """Isolate crashes per device"""
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
        enabled, message = kill_switch_active()
        if enabled:
            print(f"[BOOTSTRAP] KILL SWITCH ACTIVE: {message}")
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
        # Filter authorized devices (REMOTE)
        # -------------------------
        authorized_devices = get_authorized_devices()

        if not authorized_devices:
            print("[BOOTSTRAP] No authorized devices")
            time.sleep(BOOTSTRAP_REFRESH_SECONDS)
            continue

        print(f"[BOOTSTRAP] Authorized devices: {authorized_devices}")

        # -------------------------
        # Spawn workers
        # -------------------------
        threads = []

        for device_id in authorized_devices:
            t = threading.Thread(
                target=start_device_worker,
                args=(device_id,),
                daemon=True
            )
            t.start()
            threads.append(t)

        # -------------------------
        # Wait for workers to finish
        # -------------------------
        for t in threads:
            t.join()

        print("[BOOTSTRAP] All device cycles complete. Cooling down...")
        time.sleep(BOOTSTRAP_REFRESH_SECONDS)


def start():
    bootstrap_loop()


if __name__ == "__main__":
    start()
