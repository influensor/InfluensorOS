import os
import random

def load_random_comment(customer_id):
    path = os.path.join("data", "comments", f"{customer_id}.txt")

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        comments = [l.strip() for l in f if l.strip()]

    if not comments:
        return None

    return random.choice(comments)
