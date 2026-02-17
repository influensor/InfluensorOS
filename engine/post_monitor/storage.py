import os

DATA_DIR = "data/posts"
os.makedirs(DATA_DIR, exist_ok=True)

def get_file_path(username):
    return os.path.join(DATA_DIR, f"{username}.txt")


def load_saved_posts(username):
    path = get_file_path(username)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_posts(username, posts):
    path = get_file_path(username)
    with open(path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(post + "\n")
