import time
from datetime import datetime, timedelta

# -------------------------
# EXECUTION WINDOWS (24h)
# -------------------------

DEMO_WINDOW = {
    "start": 8,   # 10:00 AM
    "end": 23,     # 11:00 PM
}

PAID_WINDOW = {
    "start": 8,    # 8:00 AM
    "end": 23,     # 11:00 PM
}


# -------------------------
# HELPERS
# -------------------------
def _now_hour():
    return datetime.now().hour


def is_within_window(window):
    start = window["start"]
    end = window["end"]
    hour = _now_hour()

    if start <= end:
        return start <= hour < end
    else:
        # overnight window (e.g. 22 → 06)
        return hour >= start or hour < end


def seconds_until_next_window(window):
    now = datetime.now()
    start_hour = window["start"]

    next_start = now.replace(
        hour=start_hour,
        minute=0,
        second=0,
        microsecond=0,
    )

    if now.hour >= start_hour:
        next_start += timedelta(days=1)

    return max(60, int((next_start - now).total_seconds()))


# -------------------------
# PUBLIC API
# -------------------------
def enforce_execution_window(window, device_id):
    # -------------------------
    # Safety fallback
    # -------------------------
    if not window or "start" not in window or "end" not in window:
        print(f"[{device_id}] Execution window missing, skipping enforcement")
        return

    if is_within_window(window):
        return

    sleep_seconds = seconds_until_next_window(window)
    hrs = round(sleep_seconds / 3600, 2)

    print(
        f"[{device_id}] Outside execution window. "
        f"Sleeping for {hrs} hours"
    )

    time.sleep(sleep_seconds)
