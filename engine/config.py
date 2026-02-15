import os

BASE_DIR = r"C:\InfluensorOS"
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime")
DELIVERY_DIR = os.path.join(RUNTIME_DIR, "delivery")
LOGS_DIR = os.path.join(RUNTIME_DIR, "logs")
STATE_DIR = os.path.join(RUNTIME_DIR, "state")

STATE_DEVICES_DIR = os.path.join(STATE_DIR, "devices")
STATE_DEMO_DIR = os.path.join(STATE_DIR, "demo")

for d in [
    RUNTIME_DIR,
    DELIVERY_DIR,
    LOGS_DIR,
    STATE_DIR,
    STATE_DEVICES_DIR,
    STATE_DEMO_DIR,

]:
    os.makedirs(d, exist_ok=True)
