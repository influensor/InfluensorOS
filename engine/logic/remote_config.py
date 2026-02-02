import json
import time
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/influensor/InfluensorOS/main"
CACHE = {}
CACHE_TIME = {}
CACHE_TTL = 300  # 5 minutes


def _fetch_json(path):
    url = f"{BASE_URL}/{path}.json"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def get_config(path, fallback=None):
    now = time.time()

    if path in CACHE and now - CACHE_TIME.get(path, 0) < CACHE_TTL:
        return CACHE[path]

    try:
        data = _fetch_json(path)
        CACHE[path] = data
        CACHE_TIME[path] = now
        return data
    except Exception:
        return CACHE.get(path, fallback)


def kill_switch_active():
    data = get_config("kill_switch", {"enabled": False})
    return data.get("enabled", False), data.get("message", "")
