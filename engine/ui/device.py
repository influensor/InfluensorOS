import uiautomator2 as u2

_DEVICE_CACHE = {}

def get_device(adb_id):
    if adb_id not in _DEVICE_CACHE:
        d = u2.connect(adb_id)

        # IMPORTANT: enable uiautomator2 keyboard
        d.set_fastinput_ime(True)

        d.settings["wait_timeout"] = 10
        _DEVICE_CACHE[adb_id] = d

    return _DEVICE_CACHE[adb_id]
