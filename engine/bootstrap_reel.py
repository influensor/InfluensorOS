import subprocess
import threading
import time
from engine.worker_reel import worker_reel


def get_connected_devices():
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True,
        text=True
    )

    devices = []

    for line in result.stdout.splitlines():
        if "\tdevice" in line:
            device_id = line.split("\t")[0]
            devices.append(device_id)

    return devices


def start_worker(device_id):
    try:
        worker_reel(device_id)
    except Exception as e:
        print(f"[BOOTSTRAP] Worker crashed on {device_id}: {e}")


def main():
    print("[REEL BOOTSTRAP] Starting...")

    while True:
        devices = get_connected_devices()

        if not devices:
            print("[REEL BOOTSTRAP] No devices found")
            time.sleep(5)
            continue

        print(f"[REEL BOOTSTRAP] Devices: {devices}")

        threads = []

        for device_id in devices:
            t = threading.Thread(
                target=start_worker,
                args=(device_id,),
                daemon=True
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        print("[REEL BOOTSTRAP] Cycle complete, restarting...")
        time.sleep(5)


if __name__ == "__main__":
    main()