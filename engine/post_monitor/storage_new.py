import os
import json


# =====================================================
# BASE DATA DIRECTORY
# =====================================================

DATA_DIR = "data/posts"

os.makedirs(DATA_DIR, exist_ok=True)


# =====================================================
# FILE PATH
# =====================================================

def get_file_path(username):

    return os.path.join(
        DATA_DIR,
        f"{username}.json"
    )


# =====================================================
# LOAD SAVED POSTS
# =====================================================

def load_saved_posts(username):

    path = get_file_path(username)

    if not os.path.exists(path):
        return []

    try:

        with open(path, "r", encoding="utf-8") as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

    except Exception as e:

        print(
            f"[storage] failed loading "
            f"{username}: {e}"
        )

    return []


# =====================================================
# SAVE POSTS
# =====================================================

def save_posts(username, posts):

    path = get_file_path(username)

    try:

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                posts,
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            f"[storage] failed saving "
            f"{username}: {e}"
        )