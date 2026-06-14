import os
import json
from engine.config import DELIVERY_DIR

DEVICE_ID = "ZA222TB6ZX"

CUSTOMERS_DIR = "customers"
POSTS_DIR = os.path.join("data", "posts")

delivery_dir = os.path.join(DELIVERY_DIR, DEVICE_ID)

total_posts = 0
total_eligible = 0
total_completed = 0

for customer_file in os.listdir(CUSTOMERS_DIR):

    if not customer_file.endswith(".json"):
        continue

    customer_path = os.path.join(CUSTOMERS_DIR, customer_file)

    try:
        with open(customer_path, "r", encoding="utf-8") as f:
            customer = json.load(f)

        customer_id = customer.get("customer_id")

        if not customer_id:
            continue

        posts_file = os.path.join(
            POSTS_DIR,
            f"{customer_id}.json"
        )

        if not os.path.exists(posts_file):
            continue

        with open(posts_file, "r", encoding="utf-8") as f:
            posts = json.load(f)

        delivery_file = os.path.join(
            delivery_dir,
            f"{customer_id}.json"
        )

        if os.path.exists(delivery_file):
            with open(delivery_file, "r", encoding="utf-8") as f:
                delivery = json.load(f)
        else:
            delivery = {"posts": {}}

        delivery_posts = delivery.get("posts", {})

        eligible = 0
        completed = 0

        for post in posts:

            url = post.get("url")

            if not url:
                continue

            record = delivery_posts.get(url)

            if not record:
                eligible += 1
                continue

            if record.get("completed", False):
                completed += 1
            else:
                eligible += 1

        total_posts += len(posts)
        total_eligible += eligible
        total_completed += completed

        print(
            f"{customer_id}: "
            f"{eligible}/{len(posts)} eligible "
            f"(completed={completed})"
        )

    except Exception as e:
        print(f"ERROR {customer_file}: {e}")

print()
print("=" * 60)
print(f"TOTAL POSTS      : {total_posts}")
print(f"TOTAL ELIGIBLE   : {total_eligible}")
print(f"TOTAL COMPLETED  : {total_completed}")
print("=" * 60)