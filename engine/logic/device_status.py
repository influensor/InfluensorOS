import os
import json
import time
from engine.config import STATE_DIR


def _status_file(device_id):
    return os.path.join(STATE_DIR, f"{device_id}_status.json")


def load_device_status(device_id):
    path = _status_file(device_id)

    if not os.path.exists(path):
        return {
            "device_id": device_id,
            "accounts": [],
            "expected_accounts": 0,
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "device_id": device_id,
            "accounts": [],
            "expected_accounts": 0,
        }


def save_device_status(device_id, status):
    status["device_id"] = device_id
    status["updated_at"] = int(time.time())
    status["expected_accounts"] = len(status.get("accounts", []))

    path = _status_file(device_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def register_account(device_id, username):
    """
    Register username for device if not seen before.
    Returns expected_accounts count.
    """
    if not username:
        return 0

    status = load_device_status(device_id)
    accounts = status.get("accounts", [])

    if username not in accounts:
        accounts.append(username)
        status["accounts"] = accounts
        save_device_status(device_id, status)

    return len(accounts)


def get_expected_accounts(device_id):
    status = load_device_status(device_id)
    return len(status.get("accounts", []))


def get_accounts(device_id):
    status = load_device_status(device_id)
    return status.get("accounts", [])
