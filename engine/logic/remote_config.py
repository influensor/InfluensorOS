import json
import time
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/influensor/InfluensorOS/main/remote_config"

CACHE = {}
LAST_FETCH = 0
CACHE_TTL = 300  # 5 minutes


def _fetch_json(name):
    url = f"{BASE_URL}/{name}.json"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def get_config(name, fallback):
    global LAST_FETCH

    now = time.time()

    # Return cached if fresh
    if name in CACHE and now - LAST_FETCH < CACHE_TTL:
        return CACHE[name]

    try:
        data = _fetch_json(name)
        CACHE[name] = data
        LAST_FETCH = now
        return data
    except Exception:
        # Network / Git down → fallback safely
        return CACHE.get(name, fallback)


def kill_switch_active():
    data = get_config("kill_switch", {"enabled": False})
    return data.get("enabled", False), data.get("message", "")
