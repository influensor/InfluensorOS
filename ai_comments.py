import os
import random
import difflib
import json
import time
import re
from google.genai import Client
from dotenv import load_dotenv


# =====================================================
# CONFIG
# =====================================================

load_dotenv()
raw_keys = os.getenv("GEMINI_API_KEYS","")
API_KEYS = [
    line.strip()
    for line in raw_keys.splitlines()
    if line.strip()
    and not line.strip().startswith("#")
]

TOTAL_COMMENTS = 150
MODEL_NAME = "models/gemini-2.5-flash"

# =====================================================
# INFLUENSOR OS PATHS
# =====================================================

BASE_DIR = os.path.join(
    os.path.dirname(__file__),
    "data"
)

POSTS_DIR = os.path.join(
    BASE_DIR,
    "posts"
)

AI_COMMENTS_DIR = os.path.join(
    BASE_DIR,
    "ai_comments"
)

os.makedirs(
    AI_COMMENTS_DIR,
    exist_ok=True
)


# =====================================================
# COMMENT DISTRIBUTION
# =====================================================

COMMENT_DISTRIBUTION = {
    "emoji_only_or_1word": 30,
    "1_to_3_words": 30,
    "1_to_5_words": 30,
    "1_to_10_words": 30,
    "generic_short_reactions": 30
}

LANGUAGE_DISTRIBUTION = {
    "English Indian": 75,
    "Hinglish": 75
}


# =====================================================
# API ROTATION
# =====================================================

current_key_index = 0


def get_next_key():

    global current_key_index

    key = API_KEYS[current_key_index]

    current_key_index = (
        current_key_index + 1
    ) % len(API_KEYS)

    return key


def generate_with_rotation(prompt):

    for _ in range(len(API_KEYS)):

        key = get_next_key()

        try:

            client = Client(api_key=key)

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"⚠ Key Failed: "
                f"{key}..."
            )

            print(e)

            time.sleep(1)

    raise Exception(
        "❌ All API Keys Failed"
    )


# =====================================================
# SAFE JSON EXTRACTOR
# =====================================================

def extract_json(raw):

    raw = raw.strip()

    if raw.startswith("```"):

        raw = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start != -1 and end != -1:
        raw = raw[start:end]

    try:
        return json.loads(raw)

    except:
        return None


# =====================================================
# STEP 1 — NICHE DETECTOR
# =====================================================

def detect_niche(caption):

    prompt = f"""
Analyze this Instagram caption deeply.

Caption:
{caption}

Return ONLY valid JSON:

{{
  "topic": "...",
  "tone": "...",
  "energy_level": "low | medium | high",
  "intent": "promotion | entertainment | branding | personal | community"
}}
"""

    raw = generate_with_rotation(prompt)

    data = extract_json(raw)

    if data:
        return data

    return {
        "topic": "general",
        "tone": "neutral",
        "energy_level": "medium",
        "intent": "general"
    }


# =====================================================
# STEP 2 — CATEGORY DESIGN
# =====================================================

def detect_categories(caption, niche):

    prompt = f"""
We are designing realistic Instagram engagement behavior.

Caption:
{caption}

Niche Data:
{json.dumps(niche)}

Your task:
- Analyze this post deeply
- Decide realistic engagement categories
- Categories should feel human and organic
- Assign counts per category
- Total comments must equal {TOTAL_COMMENTS}
- Avoid categories related to tagging friends
- Avoid @mention or @tag based engagement
- Avoid referral or share-to-friend behavior
- Categories should focus on genuine reactions and opinions

Return ONLY valid JSON:

{{
  "categories": [
    {{
      "name": "category_name",
      "count": 20
    }}
  ]
}}
"""

    raw = generate_with_rotation(prompt)

    data = extract_json(raw)

    if data and "categories" in data:
        return validate_categories(
            data["categories"]
        )

    return [
        {
            "name": "general_reactions",
            "count": TOTAL_COMMENTS
        }
    ]


# =====================================================
# VALIDATE CATEGORY TOTAL
# =====================================================

def validate_categories(categories):

    total = sum(
        cat["count"]
        for cat in categories
    )

    if total == TOTAL_COMMENTS:
        return categories

    factor = TOTAL_COMMENTS / total

    for cat in categories:

        cat["count"] = max(
            1,
            round(cat["count"] * factor)
        )

    diff = TOTAL_COMMENTS - sum(
        cat["count"]
        for cat in categories
    )

    if diff != 0:
        categories[0]["count"] += diff

    return categories


# =====================================================
# STEP 3 — CREATE COMMENTS
# =====================================================

def create_comments(
    caption,
    niche,
    categories
):

    category_text = "\n".join([

        f"- {cat['count']} comments "
        f"focused on {cat['name']}"

        for cat in categories
    ])

    distribution_text = "\n".join([

        f"- {count} comments for "
        f"{name.replace('_', ' ')}"

        for name, count
        in COMMENT_DISTRIBUTION.items()
    ])

    language_text = "\n".join([

        f"- {count} comments in "
        f"{language}"

        for language, count
        in LANGUAGE_DISTRIBUTION.items()
    ])

    prompt = f"""
Caption:
{caption}

Niche Data:
{json.dumps(niche)}

Generate exactly {TOTAL_COMMENTS}
Instagram comments.

Category Distribution:
{category_text}

Comment Length Distribution:
{distribution_text}

Language Distribution:
{language_text}

Rules:
- Strictly create comments only in given languages
- Comments must feel organic
- Mix casual typing styles
- Some comments can feel incomplete
- Some comments can use Indian slang
- Avoid polished grammar
- Exactly 1 emoji per comment
- Emoji should match vibe
- Avoid repeating emojis
- Match tone: {niche['tone']}
- Match energy: {niche['energy_level']}
- No Comments Numbers at all
- No hashtags
- No numbering
- No markdown
- No links
- No @ mentions
- No friend tagging
- No share-to-friend comments
- One line = one comment only
- Never generate multiple comments in one line
- Never explain comments
- Never self-correct
- Never say "oops"
- Never generate variants
- Never rewrite comments
- Do not continue comments after emoji
- After one emoji STOP the line
- Output ONLY comments
"""

    return generate_with_rotation(
        prompt
    )


# =====================================================
# SPLIT BROKEN LINES
# =====================================================

def split_broken_lines(lines):

    fixed = []

    for line in lines:

        lower = line.lower()

        # ---------------------------------
        # REMOVE OOPS CHAINS
        # ---------------------------------

        if "oops" in lower:

            parts = re.split(
                r"oops.*?",
                line,
                flags=re.IGNORECASE
            )

            for part in parts:

                part = part.strip()

                if len(part) > 2:
                    fixed.append(part)

            continue

        # ---------------------------------
        # SPLIT MULTIPLE COMMENTS
        # ---------------------------------

        pieces = re.split(
            r"(?<=[😀-🙏])\s+(?=[A-Za-z])",
            line
        )

        for piece in pieces:

            piece = piece.strip()

            if len(piece) > 2:
                fixed.append(piece)

    return fixed


# =====================================================
# REMOVE MENTIONS
# =====================================================

def remove_mentions(comments):

    cleaned = []

    for comment in comments:

        if "@" in comment:
            continue

        cleaned.append(comment)

    return cleaned


# =====================================================
# CLEAN SYMBOLS
# =====================================================

ALLOWED_SYMBOLS = [
    ",",
    "?",
    ":",
    "'"
]


def clean_symbols(comment):

    comment = re.sub(
        r"[!@#$%^&*()_+=\[\]{};\"<>\\/|`~.-]",
        "",
        comment
    )

    cleaned = ""

    for char in comment:

        if (
            char.isalnum()
            or char.isspace()
            or char in ALLOWED_SYMBOLS
        ):
            cleaned += char

        else:

            # preserve emojis
            if ord(char) > 10000:
                cleaned += char

    cleaned = " ".join(
        cleaned.split()
    )

    return cleaned.strip()


# =====================================================
# CLEAN COMMENTS
# =====================================================

def clean_comments(lines):

    cleaned = []

    blocked_words = [
        "descriptive",
        "engagement",
        "reaction",
        "comments",
        "category",
        "oops",
    ]

    for line in lines:

        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        if any(
            word in lower
            for word in blocked_words
        ):
            continue

        if line.startswith("#"):
            continue

        cleaned.append(line)

    return cleaned


# =====================================================
# REMOVE SIMILAR
# =====================================================

def remove_similar(
    comments,
    threshold=0.85
):

    unique = []

    for comment in comments:

        if not any(

            difflib.SequenceMatcher(
                None,
                comment,
                u
            ).ratio() > threshold

            for u in unique
        ):
            unique.append(comment)

    return unique


# =====================================================
# ENSURE EXACT COUNT
# =====================================================

def enforce_count(comments):

    comments = comments[:TOTAL_COMMENTS]

    return comments


# =====================================================
# SAVE COMMENTS
# =====================================================

def save_comments(
    username,
    shortcode,
    comments
):

    user_dir = os.path.join(
        AI_COMMENTS_DIR,
        username
    )

    os.makedirs(
        user_dir,
        exist_ok=True
    )

    path = os.path.join(
        user_dir,
        f"{shortcode}.txt"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        for line in comments:

            f.write(line + "\n")


# =====================================================
# SAVE POSTS JSON IMMEDIATELY
# =====================================================

def save_posts_json(
    path,
    posts
):

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


# =====================================================
# PROCESS USER FILE
# =====================================================

def process_user_file(path):

    username = os.path.basename(
        path
    ).replace(".json", "")

    print(f"\n[USER] {username}")

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        posts = json.load(f)

    generated_count = 0

    # =========================================
    # PROCESS TOP 10 POSTS ONLY
    # =========================================

    for post in posts[:10]:

        # -------------------------------------
        # ONLY 1 POST PER USER PER RUN
        # -------------------------------------

        if generated_count >= 1:
            break

        # -------------------------------------
        # SKIP COMPLETED
        # -------------------------------------

        if post.get(
            "ai_comments_generated"
        ) is True:
            continue

        caption = post.get(
            "caption",
            ""
        ).strip()

        if not caption:
            continue

        shortcode = post["shortcode"]

        print(
            f"[GENERATING] "
            f"{shortcode}"
        )

        try:

            # =================================
            # NICHE
            # =================================

            print(
                "🔍 Detecting niche..."
            )

            niche = detect_niche(
                caption
            )

            print(niche)

            # =================================
            # CATEGORIES
            # =================================

            print(
                "📊 Detecting categories..."
            )

            categories = detect_categories(
                caption,
                niche
            )

            print(categories)

            # =================================
            # GENERATE COMMENTS
            # =================================

            print(
                "🤖 Generating comments..."
            )

            raw = create_comments(
                caption,
                niche,
                categories
            )

            lines = [
                line.strip()
                for line in raw.split("\n")
                if line.strip()
            ]

            lines = split_broken_lines(
                lines
            )

            lines = remove_mentions(
                lines
            )

            lines = [
                clean_symbols(line)
                for line in lines
            ]

            lines = clean_comments(
                lines
            )

            lines = remove_similar(
                lines
            )

            random.shuffle(lines)

            lines = enforce_count(
                lines
            )

            # =================================
            # SAVE COMMENTS
            # =================================

            save_comments(
                username,
                shortcode,
                lines
            )

            # =================================
            # UPDATE STATUS IMMEDIATELY
            # =================================

            post[
                "ai_comments_generated"
            ] = True

            generated_count += 1

            save_posts_json(
                path,
                posts
            )

            print(
                f"✅ Saved "
                f"{len(lines)} comments"
            )

        except Exception as e:

            print(
                f"[ERROR] "
                f"{shortcode}: {e}"
            )


# =====================================================
# MAIN
# =====================================================

def main():

    files = [

        os.path.join(
            POSTS_DIR,
            f
        )

        for f in os.listdir(
            POSTS_DIR
        )

        if f.endswith(".json")
    ]

    for path in files:

        try:

            process_user_file(path)

        except Exception as e:

            print(
                f"[FILE ERROR] "
                f"{path}: {e}"
            )


if __name__ == "__main__":
    main()