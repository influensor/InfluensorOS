import subprocess
import threading
import time

from engine.ui.switch_account import switch_account


# =========================
# GET CONNECTED DEVICES
# =========================
def get_connected_devices():
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True,
        text=True
    )

    lines = result.stdout.strip().split("\n")[1:]
    devices = []

    for line in lines:
        if "\tdevice" in line:
            devices.append(line.split("\t")[0])

    return devices


# =========================
# DEVICE WORKER
# =========================
def run_on_device(device_id):
    try:
        print(f"[{device_id}] 🚀 Starting")

        start = time.time()

        username = switch_account(device_id)

        end = time.time()

        print(f"[{device_id}] ✅ Done → {username} ({round(end - start, 2)}s)")

    except Exception as e:
        print(f"[{device_id}] ❌ Error: {e}")


# =========================
# MAIN EXECUTION
# =========================
def run_all():
    devices = get_connected_devices()

    if not devices:
        print("❌ No devices connected")
        return

    print(f"\n🔥 TOTAL DEVICES: {len(devices)}")
    print(f"📱 Devices: {devices}\n")

    threads = []

    # 🔥 START ALL AT ONCE
    for device_id in devices:
        t = threading.Thread(target=run_on_device, args=(device_id,))
        t.start()
        threads.append(t)

    # ⏳ WAIT FOR ALL
    for t in threads:
        t.join()

    print("\n✅ ALL DEVICES COMPLETED\n")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    run_all()