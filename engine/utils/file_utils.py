import os
import json
import tempfile


def safe_json_load(path, default):
    """
    Safely load JSON file.
    If file is missing, empty, or corrupted,
    return default value instead of crashing.
    """
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except Exception:
        return default


def atomic_json_write(path, data):
    """
    Atomic JSON write.
    Prevents file corruption during crashes.
    """
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        dir=directory,
        encoding="utf-8"
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name

    os.replace(temp_name, path)
