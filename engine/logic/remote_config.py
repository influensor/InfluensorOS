import json
import time
import os
import urllib.request

from engine.config import CACHE_DIR

BASE_URL = "https://raw.githubusercontent.com/influensor/InfluensorOS/main/remote_config"

CACHE_TTL = 300  # 5 minutes
CACHE_FILE = os.path.join(CACHE_DIR, "remote_config.json")

_CACHE = {}
_LAST_FETCH = 0


# -------------------------
# LOW LEVEL FETCH
# -------------------------
def _fetch_json(name):
    url = f"{BASE_URL}/{name}.json"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


# -------------------------
# DISK CACHE
# -------------------------
def _load_disk_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_disk_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# -------------------------
# PUBLIC API
# -------------------------
def get_config(name, fallback):
    global _LAST_FETCH, _CACHE

    now = time.time()

    # In-memory cache still valid
    if name in _CACHE and now - _LAST_FETCH < CACHE_TTL:
        return _CACHE[name]

    # Load disk cache (once)
    if not _CACHE:
        _CACHE = _load_disk_cache()

    try:
        data = _fetch_json(name)

        _CACHE[name] = data
        _LAST_FETCH = now

        _save_disk_cache(_CACHE)
        return data

    except Exception:
        # Network down → disk cache → fallback
        return _CACHE.get(name, fallback)


def kill_switch_active():
    data = get_config("kill_switch", {"enabled": False})
    return data.get("enabled", False), data.get("message", "")
