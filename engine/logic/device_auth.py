import subprocess
import json
import os


# =========================
# ADB DEVICE DETECTION
# =========================
def get_connected_adb_devices():
    """
    Returns a list of connected ADB device IDs
    """
    try:
        result = subprocess.check_output(
            ["adb", "devices"],
            stderr=subprocess.STDOUT,
            text=True
        )
    except Exception as e:
        print(f"[device_auth] adb not available: {e}")
        return []

    devices = []
    for line in result.splitlines():
        if "\tdevice" in line:
            devices.append(line.split("\t")[0])

    return devices


# =========================
# LOAD ALLOWED DEVICES
# =========================
def load_allowed_devices(path="devices/allowed_devices.json"):
    if not os.path.exists(path):
        print("[device_auth] allowed_devices.json not found")
        return {"devices": []}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# FILTER AUTHORIZED DEVICES
# =========================
def filter_authorized(connected_devices, allowed_config):
    allowed = set()

    for d in allowed_config.get("devices", []):
        if d.get("active"):
            allowed.add(d.get("adb_id"))

    return [d for d in connected_devices if d in allowed]
