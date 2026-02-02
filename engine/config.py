import os

BASE_DIR = r"C:\InfluensorOS"
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime")

ACCOUNTS_DIR = os.path.join(RUNTIME_DIR, "accounts")
DELIVERY_DIR = os.path.join(RUNTIME_DIR, "delivery")
STATE_DIR = os.path.join(RUNTIME_DIR, "state")
LOGS_DIR = os.path.join(RUNTIME_DIR, "logs")
CACHE_DIR = os.path.join(RUNTIME_DIR, "cache")

for d in [
    RUNTIME_DIR,
    ACCOUNTS_DIR,
    DELIVERY_DIR,
    STATE_DIR,
    LOGS_DIR,
    CACHE_DIR,
]:
    os.makedirs(d, exist_ok=True)
