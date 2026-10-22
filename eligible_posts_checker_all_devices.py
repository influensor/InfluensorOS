import os
import json
import subprocess
from engine.config import DELIVERY_DIR

CUSTOMERS_DIR = "customers"
POSTS_DIR = os.path.join("data", "posts")


def get_connected_devices():
    """Return ADB devices whose state is 'device'."""
    try:
        output = subprocess.check_output(
            ["adb", "devices"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        print("[ERROR] ADB was not found. Make sure adb is installed and on PATH.")
        return []
    except Exception as exc:
        print(f"[ERROR] Could not get ADB devices: {exc}")
        return []

    devices = []
    for line in output.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])

    return devices


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default
    except Exception as exc:
        print(f"[ERROR] Could not read {path}: {exc}")
        return default


def get_post_label(post):
    shortcode = post.get("shortcode")
    url = post.get("url", "")
    if shortcode:
        return f"{shortcode} | {url}"
    return url


def check_device(device_id, customer_files):
    print("\n" + "=" * 80)
    print(f"DEVICE: {device_id}")
    print("=" * 80)

    device_delivery_dir = os.path.join(DELIVERY_DIR, device_id)
    device_total_posts = 0
    device_total_eligible = 0
    device_total_completed = 0
    customers_checked = 0

    for customer_file in customer_files:
        customer_path = os.path.join(CUSTOMERS_DIR, customer_file)
        customer = load_json(customer_path, None)

        if not isinstance(customer, dict):
            print(f"[SKIP] {customer_file}: invalid customer JSON")
            continue

        customer_id = customer.get("customer_id")
        if not customer_id:
            print(f"[SKIP] {customer_file}: missing customer_id")
            continue

        posts_file = os.path.join(POSTS_DIR, f"{customer_id}.json")
        if not os.path.exists(posts_file):
            continue

        posts = load_json(posts_file, [])
        if not isinstance(posts, list):
            print(f"[SKIP] {customer_id}: posts file is not a list")
            continue

        delivery_file = os.path.join(
            device_delivery_dir,
            f"{customer_id}.json",
        )
        delivery = load_json(delivery_file, {"posts": {}})
        if not isinstance(delivery, dict):
            delivery = {"posts": {}}

        delivery_posts = delivery.get("posts", {})
        if not isinstance(delivery_posts, dict):
            delivery_posts = {}

        eligible_posts = []
        completed = 0
        valid_posts = 0

        for post in posts:
            if not isinstance(post, dict):
                continue

            url = post.get("url")
            if not url:
                continue

            valid_posts += 1
            record = delivery_posts.get(url)

            if isinstance(record, dict) and record.get("completed", False):
                completed += 1
            else:
                eligible_posts.append(post)

        customers_checked += 1
        device_total_posts += valid_posts
        device_total_eligible += len(eligible_posts)
        device_total_completed += completed

        print(
            f"\nCUSTOMER: {customer_id} | "
            f"Eligible: {len(eligible_posts)}/{valid_posts} | "
            f"Completed: {completed}"
        )

        if eligible_posts:
            print("Eligible posts:")
            for index, post in enumerate(eligible_posts, start=1):
                print(f"  {index}. {get_post_label(post)}")
        else:
            print("Eligible posts: none")

    print("\n" + "-" * 80)
    print(f"DEVICE SUMMARY: {device_id}")
    print(f"Customers checked : {customers_checked}")
    print(f"Total posts       : {device_total_posts}")
    print(f"Total eligible    : {device_total_eligible}")
    print(f"Total completed   : {device_total_completed}")
    print("-" * 80)

    return {
        "posts": device_total_posts,
        "eligible": device_total_eligible,
        "completed": device_total_completed,
        "customers": customers_checked,
    }


def main():
    if not os.path.isdir(CUSTOMERS_DIR):
        print(f"[ERROR] Customers directory not found: {CUSTOMERS_DIR}")
        return

    customer_files = sorted(
        name for name in os.listdir(CUSTOMERS_DIR)
        if name.endswith(".json")
    )

    if not customer_files:
        print("[INFO] No customer JSON files found.")
        return

    devices = get_connected_devices()
    if not devices:
        print("[INFO] No connected ADB devices found.")
        return

    print(f"Connected devices found: {len(devices)}")
    for device in devices:
        print(f" - {device}")

    all_totals = {
        "posts": 0,
        "eligible": 0,
        "completed": 0,
        "customers": 0,
    }

    for device_id in devices:
        totals = check_device(device_id, customer_files)
        for key in all_totals:
            all_totals[key] += totals[key]

    print("\n" + "=" * 80)
    print("ALL-DEVICE TOTALS")
    print("=" * 80)
    print(f"Devices checked    : {len(devices)}")
    print(f"Customer checks    : {all_totals['customers']}")
    print(f"Total posts        : {all_totals['posts']}")
    print(f"Total eligible     : {all_totals['eligible']}")
    print(f"Total completed    : {all_totals['completed']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
