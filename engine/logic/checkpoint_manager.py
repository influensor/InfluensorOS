import os
from engine.config import STATE_DEVICES_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write


def _path(device_id):
    folder = os.path.join(STATE_DEVICES_DIR, device_id)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "checkpoint.json")


def load(device_id):
    return safe_json_load(_path(device_id), None)


def save(device_id, data):
    atomic_json_write(_path(device_id), data)


def clear(device_id):
    path = _path(device_id)
    if os.path.exists(path):
        os.remove(path)
