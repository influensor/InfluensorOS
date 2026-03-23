import time
import random
from engine.ui.device import get_device


# =========================
# CORE SWIPE ENGINE
# =========================
def _swipe(device_id, start_x, start_y, end_x, end_y, duration=0.03):
    d = get_device(device_id)

    try:
        d.swipe(start_x, start_y, end_x, end_y, duration=duration)
    except Exception:
        # fallback to swipe_ext (more natural)
        direction = "up" if end_y < start_y else "down"
        d.swipe_ext(direction, scale=0.9)

    time.sleep(random.uniform(0.5, 1.2))


# =========================
# PUBLIC FUNCTIONS
# =========================
def swipe_up(device_id, fast=True):
    d = get_device(device_id)
    w, h = d.window_size()

    duration = 0.02 if fast else 0.06

    _swipe(
        device_id,
        w // 2,
        int(h * 0.80),
        w // 2,
        int(h * 0.20),
        duration
    )


def swipe_down(device_id, fast=True):
    d = get_device(device_id)
    w, h = d.window_size()

    duration = 0.02 if fast else 0.06

    _swipe(
        device_id,
        w // 2,
        int(h * 0.20),
        w // 2,
        int(h * 0.80),
        duration
    )


def swipe_left(device_id, fast=True):
    d = get_device(device_id)
    w, h = d.window_size()

    duration = 0.02 if fast else 0.06

    _swipe(
        device_id,
        int(w * 0.80),
        h // 2,
        int(w * 0.20),
        h // 2,
        duration
    )


def swipe_right(device_id, fast=True):
    d = get_device(device_id)
    w, h = d.window_size()

    duration = 0.02 if fast else 0.06

    _swipe(
        device_id,
        int(w * 0.20),
        h // 2,
        int(w * 0.80),
        h // 2,
        duration
    )