import os
import random


def load_random_comment(customer_id=None):
    """
    Priority:
    1️⃣ Customer-specific comments → data/comments/{customer_id}.txt
    2️⃣ Generic comments → data/comments/generic.txt
    """

    paths = []

    # -------------------------
    # 1️⃣ Customer-specific file
    # -------------------------
    if customer_id:
        paths.append(os.path.join("data", "comments", f"{customer_id}.txt"))

    # -------------------------
    # 2️⃣ Generic fallback file
    # -------------------------
    paths.append(os.path.join("data", "comments", "generic.txt"))

    # -------------------------
    # Load first available
    # -------------------------
    for path in paths:
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            comments = [l.strip() for l in f if l.strip()]

        if comments:
            return random.choice(comments)

    return None