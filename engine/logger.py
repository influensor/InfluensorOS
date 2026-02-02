import os
import threading
from datetime import datetime

from engine.config import LOGS_DIR

_lock = threading.Lock()


def _log_file():
    """
    One log file per day
    Example: 02-02-2026.log
    """
    date_str = datetime.now().strftime("%d-%m-%Y")
    return os.path.join(LOGS_DIR, f"{date_str}.log")


def log(message, device_id=None, level="INFO"):
    """
    Central logging function

    level: INFO | WARN | ERROR | DEBUG
    """
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    prefix = f"[{timestamp}] [{level}]"
    if device_id:
        prefix += f" [{device_id}]"

    line = f"{prefix} {message}"

    # Console output
    print(line)

    # File output (must never crash engine)
    with _lock:
        try:
            with open(_log_file(), "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


# -------------------------
# Convenience helpers
# -------------------------
def info(msg, device_id=None):
    log(msg, device_id, "INFO")


def warn(msg, device_id=None):
    log(msg, device_id, "WARN")


def error(msg, device_id=None):
    log(msg, device_id, "ERROR")


def debug(msg, device_id=None):
    log(msg, device_id, "DEBUG")
