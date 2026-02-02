import os
import json
import subprocess
import platform

from engine.config import BASE_DIR


# --------------------------------------------------
# SYSTEM IDENTIFICATION
# --------------------------------------------------
def get_system_name():
    return os.environ.get("COMPUTERNAME") or platform.node()


# --------------------------------------------------
# SYSTEM-SCOPED DEVICE AUTH FILE
# --------------------------------------------------
def _system_devices_file():
    system = get_system_name()
    return os.path.join(BASE_DIR, "allowed_devices", f"{system}.json")


def load_system_authorized_devices():
    """
    System is authorized ONLY if this file exists
    """
    path = _system_devices_file()

    if not os.path.exists(path):
        return None  # system NOT authorized

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("authorized_devices", [])


# --------------------------------------------------
# ADB HELPERS
# --------------------------------------------------
def get_connected_adb_devices():
    try:
        out = subprocess.check_output(
            ["adb", "devices"],
            stderr=subprocess.DEVNULL
        ).decode()

        lines = out.strip().splitlines()[1:]
        return [
            line.split("\t")[0]
            for line in lines
            if "\tdevice" in line
        ]
    except Exception:
        return []


# --------------------------------------------------
# FINAL AUTH API (USED EVERYWHERE)
# --------------------------------------------------
def get_authorized_devices():
    allowed = load_system_authorized_devices()
    if allowed is None:
        return []  # system not authorized

    connected = set(get_connected_adb_devices())
    return list(connected & set(allowed))


# --------------------------------------------------
# BACKWARD COMPAT (BOOTSTRAP)
# --------------------------------------------------
def filter_authorized(connected_devices, allowed_devices=None):
    if not allowed_devices:
        return connected_devices
    return [d for d in connected_devices if d in allowed_devices]
