import subprocess

# -------------------------
# GET ALL CONNECTED DEVICES
# -------------------------
def get_devices():
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    
    return [
        line.split("\t")[0]
        for line in result.stdout.splitlines()
        if "\tdevice" in line
    ]


# -------------------------
# YOUR URL LIST
# -------------------------
urls = [
"https://www.instagram.com/p/DTw7MToABH_/",
"https://www.instagram.com/p/DWFFlMCk9qF/",
"https://www.instagram.com/p/DWKDxHsk36h/",
"https://www.instagram.com/p/DWM0wBGk4DD/",
"https://www.instagram.com/p/DVjTrv2E__g/",
"https://www.instagram.com/p/DVRCl4yEZSi/",
"https://www.instagram.com/p/DVBlIhCAp0q/",
"https://www.instagram.com/p/DUyF91QEgJV/",
"https://www.instagram.com/p/DVLGXLLiKg9/",
"https://www.instagram.com/p/DV_kfseibJ7/",
"https://www.instagram.com/p/DWCS_zwkinb/",
"https://www.instagram.com/p/DV_BOzXE9hr/",
"https://www.instagram.com/p/DWLO0SSDCNf/",
"https://www.instagram.com/p/DWJGc5MCJKC/",
"https://www.instagram.com/p/DVjZMloDMsL/",
"https://www.instagram.com/p/DVgsvvCAWlU/",
"https://www.instagram.com/p/DWCIyvAEyFR/",
]


# -------------------------
# EXECUTION
# -------------------------
devices = get_devices()

print(f"Devices found: {devices}")

for device_id, url in zip(devices, urls):
    print(f"[{device_id}] Opening → {url}")

    subprocess.run([
        "adb", "-s", device_id,
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", url,
        "-p", "com.instagram.android"
    ])
