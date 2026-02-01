import os

def load_posts(customer_id):
    path = os.path.join("data", "posts", f"{customer_id}.txt")

    if not os.path.exists(path):
        print(f"[post_loader] post file missing: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
