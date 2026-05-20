import os
import json
import random


# =====================================================
# PATHS
# =====================================================

POSTS_DIR = os.path.join(
    "data",
    "posts"
)

COMMENTS_DIR = os.path.join(
    "data",
    "comments"
)

AI_COMMENTS_DIR = os.path.join(
    "data",
    "ai_comments"
)


# =====================================================
# POSTS FILE
# =====================================================

def get_posts_path(customer_id):

    return os.path.join(
        POSTS_DIR,
        f"{customer_id}.json"
    )


# =====================================================
# LOAD POSTS
# =====================================================

def load_posts(customer_id):

    path = get_posts_path(
        customer_id
    )

    if not os.path.exists(path):
        return []

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

    except Exception as e:

        print(
            f"[comment_loader] "
            f"failed loading posts "
            f"{customer_id}: {e}"
        )

    return []


# =====================================================
# SAVE POSTS
# =====================================================

def save_posts(
    customer_id,
    posts
):

    path = get_posts_path(
        customer_id
    )

    try:

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                posts,
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            f"[comment_loader] "
            f"failed saving posts "
            f"{customer_id}: {e}"
        )


# =====================================================
# LOAD TXT COMMENTS
# =====================================================

def load_txt_comments(path):

    if not os.path.exists(path):
        return []

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            comments = [

                line.strip()

                for line in f

                if line.strip()
            ]

        return comments

    except Exception as e:

        print(
            f"[comment_loader] "
            f"failed loading comments "
            f"{path}: {e}"
        )

    return []


# =====================================================
# SAVE TXT COMMENTS
# =====================================================

def save_txt_comments(
    path,
    comments
):

    try:

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            for comment in comments:

                f.write(
                    comment + "\n"
                )

    except Exception as e:

        print(
            f"[comment_loader] "
            f"failed saving comments "
            f"{path}: {e}"
        )


# =====================================================
# RANDOM COMMENT
# =====================================================

def get_random_comment(comments):

    if not comments:
        return None

    return random.choice(comments)


# =====================================================
# REMOVE USED COMMENT
# =====================================================

def remove_used_comment(
    comments,
    used_comment
):

    updated = comments.copy()

    try:

        updated.remove(
            used_comment
        )

    except:
        pass

    return updated


# =====================================================
# AI COMMENT FILE
# =====================================================

def get_ai_comment_path(
    customer_id,
    shortcode
):

    return os.path.join(

        AI_COMMENTS_DIR,

        customer_id,

        f"{shortcode}.txt"
    )


# =====================================================
# CUSTOMER COMMENT FILE
# =====================================================

def get_customer_comment_path(
    customer_id
):

    return os.path.join(

        COMMENTS_DIR,

        f"{customer_id}.txt"
    )


# =====================================================
# GENERIC COMMENT FILE
# =====================================================

def get_generic_comment_path():

    return os.path.join(

        COMMENTS_DIR,

        "generic.txt"
    )


# =====================================================
# LOAD AI COMMENT
# =====================================================

def load_ai_comment(
    customer_id,
    shortcode
):

    path = get_ai_comment_path(
        customer_id,
        shortcode
    )

    comments = load_txt_comments(
        path
    )

    if not comments:
        return None

    comment = get_random_comment(
        comments
    )

    if not comment:
        return None

    # -----------------------------------------
    # REMOVE USED COMMENT
    # -----------------------------------------

    updated_comments = remove_used_comment(
        comments,
        comment
    )

    save_txt_comments(
        path,
        updated_comments
    )

    return comment


# =====================================================
# LOAD CUSTOMER COMMENT
# =====================================================

def load_customer_comment(
    customer_id
):

    path = get_customer_comment_path(
        customer_id
    )

    comments = load_txt_comments(
        path
    )

    return get_random_comment(
        comments
    )


# =====================================================
# LOAD GENERIC COMMENT
# =====================================================

def load_generic_comment():

    path = get_generic_comment_path()

    comments = load_txt_comments(
        path
    )

    return get_random_comment(
        comments
    )


# =====================================================
# FIND POST
# =====================================================

def find_post(
    customer_id,
    shortcode
):

    posts = load_posts(
        customer_id
    )

    for post in posts:

        if post.get(
            "shortcode"
        ) == shortcode:

            return post

    return None


# =====================================================
# MAIN COMMENT LOADER
# =====================================================

def load_random_comment(
    customer_id=None,
    shortcode=None
):

    # =================================================
    # AI COMMENT PRIORITY
    # =================================================

    if customer_id and shortcode:

        post = find_post(
            customer_id,
            shortcode
        )

        if post:

            ai_ready = post.get(
                "ai_comments_generated",
                False
            )

            if ai_ready:

                ai_comment = load_ai_comment(

                    customer_id,

                    shortcode
                )

                if ai_comment:

                    return ai_comment

    # =================================================
    # CUSTOMER COMMENTS
    # =================================================

    if customer_id:

        customer_comment = (
            load_customer_comment(
                customer_id
            )
        )

        if customer_comment:

            return customer_comment

    # =================================================
    # GENERIC FALLBACK
    # =================================================

    generic_comment = (
        load_generic_comment()
    )

    if generic_comment:

        return generic_comment

    return None