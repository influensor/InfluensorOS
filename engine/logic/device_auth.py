import os
import json
import subprocess
import platform

from engine.config import BASE_DIR


# ==================================================
# SYSTEM IDENTIFICATION
# ==================================================
def get_system_name():
    name = os.environ.get("COMPUTERNAME") or platform.node()
    return name.strip().lower()


# ==================================================
# SYSTEM-SCOPED AUTH FILE
# ==================================================
def _system_devices_file():
    """
    Example:
    C:\\InfluensorOS\\allowed_devices\\blackaquaindia.json
    """
    system = get_system_name()
    return os.path.join(
        BASE_DIR,
        "allowed_devices",
        f"{system}.json"
    )


def load_system_authorized_devices():
    """
    STRICT MODE:
    - System is authorized ONLY if system JSON exists
    - No fallback
    """
    path = _system_devices_file()

    if not os.path.exists(path):
        return None  # system NOT authorized

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    return data.get("authorized_devices", [])


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
# FINAL AUTH API (USED EVERYWHERE)
# ==================================================
def get_authorized_devices():
    """
    Final gate:
    - system JSON must exist
    - device must be listed
    - device must be connected
    """
    allowed = load_system_authorized_devices()
    if not allowed:
        return []

    connected = set(get_connected_adb_devices())
    return list(connected & set(allowed))


# ==================================================
# BACKWARD COMPAT (BOOTSTRAP SAFETY)
# ==================================================
def filter_authorized(connected_devices, allowed_devices=None):
    """
    Bootstrap compatibility.
    STRICT MODE: only system JSON matters.
    """
    authorized = set(get_authorized_devices())
    return [d for d in connected_devices if d in authorized]


def load_allowed_devices():
    """
    Legacy API — intentionally disabled.
    Returns None to prevent fallback.
    """
    return None
