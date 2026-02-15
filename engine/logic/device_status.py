import os
import time
from engine.config import STATE_DEVICES_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write


def _status_file(device_id):
    folder = os.path.join(STATE_DEVICES_DIR, device_id)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "device_status.json")


def load_device_status(device_id):
    return safe_json_load(_status_file(device_id), {
        "device_id": device_id,
        "accounts": [],
        "expected_accounts": 0,
    })


def save_device_status(device_id, status):
    status["device_id"] = device_id
    status["updated_at"] = int(time.time())
    status["expected_accounts"] = len(status.get("accounts", []))
    atomic_json_write(_status_file(device_id), status)


def register_account(device_id, username):
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
    return len(load_device_status(device_id).get("accounts", []))


def get_accounts(device_id):
    return load_device_status(device_id).get("accounts", [])
