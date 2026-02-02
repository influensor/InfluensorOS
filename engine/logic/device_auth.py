import os
import platform
import subprocess

from engine.logic.remote_config import get_config, kill_switch_active


# ==================================================
# SYSTEM IDENTIFICATION
# ==================================================
def get_system_name():
    name = os.environ.get("COMPUTERNAME") or platform.node()
    return name.strip().lower()


# ==================================================
# ADB HELPERS
# ==================================================
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


# ==================================================
# REMOTE AUTHORIZATION (GITHUB)
# ==================================================
def load_system_authorized_devices():
    system = get_system_name()

    # Emergency kill switch
    enabled, _ = kill_switch_active()
    if enabled:
        return None

    # Fetch system-specific config
    data = get_config(f"devices/{system}", fallback=None)

    if not data:
        return None

    if not data.get("enabled", True):
        return None

    return data.get("authorized_devices", [])


def get_authorized_devices():
    allowed = load_system_authorized_devices()
    if not allowed:
        return []

    connected = set(get_connected_adb_devices())
    return list(connected & set(allowed))


# ==================================================
# BOOTSTRAP COMPATIBILITY
# ==================================================
def filter_authorized(connected_devices, allowed_devices=None):
    authorized = set(get_authorized_devices())
    return [d for d in connected_devices if d in authorized]


def load_allowed_devices():
    # Legacy API intentionally disabled
    return None
