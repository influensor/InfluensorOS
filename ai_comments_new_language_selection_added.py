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
raw_keys = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [
    line.strip()
    for line in raw_keys.splitlines()
    if line.strip() and not line.strip().startswith("#")
]
# Randomize order every run
random.shuffle(API_KEYS)

TOTAL_COMMENTS = 150
#MODEL_NAME = "models/gemini-2.5-flash"
MODEL_NAME = "models/gemini-3.5-flash"

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

# Customer JSON files are supported in either project-root/customers
# or data/customers, preserving the existing customer JSON structure.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMER_DIR_CANDIDATES = [
    os.path.join(PROJECT_DIR, "customers"),
    os.path.join(BASE_DIR, "customers"),
]

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

# Default used when a customer JSON has no valid custom distribution.
# Existing customer JSON files do not need to be changed.
DEFAULT_LANGUAGE_DISTRIBUTION = {
    "English Indian": 75,
    "Hinglish": 75,
}

# =====================================================
# API ROTATION
# =====================================================

current_key_index = 0


def get_next_key():

    global current_key_index

    if not API_KEYS:
        raise RuntimeError(
            "No Gemini API keys found. Set GEMINI_API_KEYS in your .env file."
        )

    key = API_KEYS[current_key_index]

    current_key_index = (
        current_key_index + 1
    ) % len(API_KEYS)

    return key


def generate_with_rotation(prompt):

    if not API_KEYS:
        raise RuntimeError(
            "No Gemini API keys found. Set GEMINI_API_KEYS in your .env file."
        )

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
# CUSTOMER LANGUAGE DISTRIBUTION
# =====================================================

def find_customer_file(username):
    """Find a customer JSON by filename or username/customer_id field."""
    for directory in CUSTOMER_DIR_CANDIDATES:
        if not os.path.isdir(directory):
            continue

        direct_path = os.path.join(directory, f"{username}.json")
        if os.path.isfile(direct_path):
            return direct_path

        # Fallback: filename may differ from the username.
        for filename in os.listdir(directory):
            if not filename.lower().endswith(".json"):
                continue
            candidate = os.path.join(directory, filename)
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    customer = json.load(f)
                if (
                    str(customer.get("username", "")).lower() == username.lower()
                    or str(customer.get("customer_id", "")).lower() == username.lower()
                ):
                    return candidate
            except Exception as e:
                print(f"[CUSTOMER JSON WARNING] {filename}: {e}")

    return None


def allocate_language_counts(distribution, total_comments=TOTAL_COMMENTS):
    """Convert percentages to whole-number counts totaling exactly total_comments."""
    exact_counts = {
        language: (weight / 100.0) * total_comments
        for language, weight in distribution.items()
    }
    counts = {
        language: int(value)
        for language, value in exact_counts.items()
    }
    remainder = total_comments - sum(counts.values())

    # Largest-remainder method ensures the final count is exact.
    ranked = sorted(
        exact_counts,
        key=lambda language: exact_counts[language] - counts[language],
        reverse=True,
    )
    for language in ranked[:remainder]:
        counts[language] += 1

    return {language: count for language, count in counts.items() if count > 0}


def get_customer_language_distribution(username):
    """Read arbitrary language labels and percentage weights from customer JSON.

    Language labels are passed directly to Gemini. No language allowlist or
    alias mapping is used. Missing/invalid settings use the legacy defaults.
    """
    customer_path = find_customer_file(username)
    if not customer_path:
        print(f"[LANGUAGE] No customer JSON found for {username}; using defaults.")
        return dict(DEFAULT_LANGUAGE_DISTRIBUTION)

    try:
        with open(customer_path, "r", encoding="utf-8") as f:
            customer = json.load(f)

        settings = customer.get("settings", {})
        custom = settings.get("comment_language_distribution")

        if custom is None:
            print(f"[LANGUAGE] No custom language distribution; using defaults for {username}.")
            return dict(DEFAULT_LANGUAGE_DISTRIBUTION)

        if not isinstance(custom, dict) or not custom:
            raise ValueError("comment_language_distribution must be a non-empty JSON object")

        percentages = {}
        for raw_language, raw_weight in custom.items():
            if not isinstance(raw_language, str) or not raw_language.strip():
                raise ValueError("Language labels must be non-empty strings")
            if isinstance(raw_weight, bool) or not isinstance(raw_weight, (int, float)):
                raise ValueError(f"Weight for {raw_language} must be numeric")
            if raw_weight < 0:
                raise ValueError(f"Weight for {raw_language} cannot be negative")
            # A zero-weight language is intentionally disabled; skip it.
            if raw_weight == 0:
                continue
            percentages[raw_language.strip()] = float(raw_weight)

        if not percentages:
            raise ValueError("At least one language must have a weight greater than zero")

        total_weight = sum(percentages.values())
        if abs(total_weight - 100.0) > 0.01:
            raise ValueError(f"Language weights must total 100%; got {total_weight:g}%")

        # Convert percentages to exact whole-comment counts.
        return allocate_language_counts(percentages, TOTAL_COMMENTS)

    except Exception as e:
        print(f"[LANGUAGE WARNING] Invalid distribution for {username}: {e}")
        print("[LANGUAGE] Falling back to default English/Hinglish distribution.")
        return dict(DEFAULT_LANGUAGE_DISTRIBUTION)


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

def detect_categories(caption, niche, total_comments=TOTAL_COMMENTS):

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
- Total comments must equal {total_comments}
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
            data["categories"],
            total_comments
        )

    return [
        {
            "name": "general_reactions",
            "count": total_comments
        }
    ]


# =====================================================
# VALIDATE CATEGORY TOTAL
# =====================================================

def validate_categories(categories, total_comments=TOTAL_COMMENTS):
    """Normalize category counts and guarantee their sum matches total_comments."""
    if not isinstance(categories, list) or not categories:
        return [{"name": "general_reactions", "count": total_comments}]

    valid_categories = []
    for category in categories:
        if not isinstance(category, dict) or not category.get("name"):
            continue
        try:
            count = int(category.get("count", 0))
        except (TypeError, ValueError):
            continue
        if count > 0:
            valid_categories.append({"name": str(category["name"]), "count": count})

    if not valid_categories:
        return [{"name": "general_reactions", "count": total_comments}]

    total = sum(category["count"] for category in valid_categories)
    if total == total_comments:
        return valid_categories

    exact_counts = [category["count"] * total_comments / total for category in valid_categories]
    rounded_counts = [int(value) for value in exact_counts]
    remainder = total_comments - sum(rounded_counts)
    order = sorted(
        range(len(exact_counts)),
        key=lambda index: exact_counts[index] - rounded_counts[index],
        reverse=True,
    )
    for index in order[:remainder]:
        rounded_counts[index] += 1

    for category, count in zip(valid_categories, rounded_counts):
        category["count"] = count

    return [category for category in valid_categories if category["count"] > 0]


# =====================================================
# STEP 3 — CREATE COMMENTS
# =====================================================

def create_comments(
    caption,
    niche,
    categories,
    language_distribution
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
        in language_distribution.items()
    ])

    total_comments = sum(language_distribution.values())

    language_detail_text = "\\n".join(
        f"- {language}: Use the language and writing script explicitly described by this label. "
        f"If the label names a script, follow that script exactly."
        for language in language_distribution
    )

    prompt = f"""
Caption:
{caption}

Niche Data:
{json.dumps(niche)}

Generate exactly {total_comments}
Instagram comments.

Category Distribution:
{category_text}

Comment Length Distribution:
{distribution_text}

Language Distribution (EXACT COUNTS — must be followed):
{language_text}

Language/script requirements:
{language_detail_text}

The count beside each language is the exact number required for that language.
The total across all languages is {total_comments}. Do not rebalance or substitute languages.

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

CRITICAL:
- Never append labels, tags, codes or metadata.
- Never append category names.
- Never append language codes.
- Never append abbreviations like ERM, SPR, AFA, HAC, RVS, L1, L2, L3, L4, L5, ENIN or similar.
- Every line must contain ONLY the comment text.
- After the emoji, immediately end the line.
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
            parts = re.split(r"oops.*?",line,flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if len(part) > 2:
                    fixed.append(part)
            continue

        # ---------------------------------
        # SPLIT MULTIPLE COMMENTS
        # ---------------------------------

        pieces = re.split(r"(?<=[😀-🙏])\s+(?=[A-Za-z])",line)
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

import unicodedata
def clean_symbols(comment):
    cleaned = ""
    for char in comment:
        category = unicodedata.category(char)
        # Keep letters, numbers,
        # punctuation, spaces,
        # emojis and combining marks
        if (
            char.isspace()
            or char in ALLOWED_SYMBOLS
            or category.startswith("L")   # Letters
            or category.startswith("N")   # Numbers
            or category.startswith("M")   # Combining marks (Marathi matras)
            or ord(char) > 10000          # Emojis
        ):
            cleaned += char
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()

# =====================================================
# CLEAN COMMENTS
# =====================================================

def clean_comments(lines):
    cleaned = []
    blocked_words = ["descriptive","engagement","reaction","comments","category","oops","example","invalid","valid","rules","instruction","english","hinglish","hindi",]

    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if any(word in lower for word in blocked_words):
            continue
        if line.startswith("#"):
            continue
        cleaned.append(line)
    return cleaned


# =====================================================
# REMOVE NUMBERING ONLY IF ENTIRE BATCH IS NUMBERED
# =====================================================

def remove_batch_numbering(comments):
    if not comments:
        return comments

    number_pattern = re.compile(r"^\s*\d+\s+")
    numbered_count = sum(1 for comment in comments if number_pattern.match(comment))

    # Only remove numbers when EVERY comment
    # starts with a number.
    if numbered_count == len(comments):
        print(f"🔢 Detected numbering in all " f"{len(comments)} comments — removing numbers")

        cleaned = []
        for comment in comments:
            comment = number_pattern.sub("",comment,count=1).strip()
            cleaned.append(comment)
        return cleaned

    print(f"🔢 Mixed/normal output detected " f"({numbered_count}/{len(comments)} numbered) " f"— keeping numbers")
    return comments

# =====================================================
# REMOVE SIMILAR
# =====================================================

def remove_similar(comments,threshold=0.85):
    unique = []
    for comment in comments:
        if not any(difflib.SequenceMatcher(None,comment,u).ratio() > threshold for u in unique):
            unique.append(comment)
    return unique

# =====================================================
# ENSURE EXACT COUNT
# =====================================================

def enforce_count(comments, total_comments=TOTAL_COMMENTS):
    return comments[:total_comments]

# =====================================================
# SAVE COMMENTS
# =====================================================

def save_comments(username,shortcode,comments):
    user_dir = os.path.join(AI_COMMENTS_DIR,username)
    os.makedirs(user_dir,exist_ok=True)
    path = os.path.join(user_dir,f"{shortcode}.txt")
    with open(path,"w",encoding="utf-8") as f:
        for line in comments:
            f.write(line + "\n")

# =====================================================
# SAVE POSTS JSON IMMEDIATELY
# =====================================================

def save_posts_json(path,posts):
    with open(path,"w",encoding="utf-8") as f:
        json.dump(posts,f,indent=2,ensure_ascii=False)

# =====================================================
# PROCESS USER FILE
# =====================================================

def process_user_file(path):
    username = os.path.basename(path).replace(".json", "")
    print(f"\n[USER] {username}")
    with open(path,"r",encoding="utf-8") as f:
        posts = json.load(f)
    
    generated_count = 0

    # =========================================
    # PROCESS TOP 10 POSTS ONLY
    # =========================================

    for post in posts[:100]:
        # -------------------------------------
        # ONLY 1 POST PER USER PER RUN
        # -------------------------------------
        
        if generated_count >= 1:
            break
        
        # -------------------------------------
        # SKIP COMPLETED
        # -------------------------------------
        
        if post.get("ai_comments_generated") is True:
            continue

        caption = post.get("caption","").strip()
        if not caption:
            continue

        shortcode = post["shortcode"]
        print(f"[GENERATING] " f"{shortcode}")

        try:

            # =================================
            # NICHE
            # =================================

            print("🔍 Detecting niche...")
            niche = detect_niche(caption)
            print(niche)

            # =================================
            # CUSTOMER LANGUAGE DISTRIBUTION
            # =================================

            language_distribution = get_customer_language_distribution(username)
            total_comments = sum(language_distribution.values())
            print(f"🌐 Language distribution ({total_comments} comments): {language_distribution}")

            # =================================
            # CATEGORIES
            # =================================

            print("📊 Detecting categories...")
            categories = detect_categories(caption, niche, total_comments)
            print(categories)

            # =================================
            # GENERATE COMMENTS
            # =================================

            print("🤖 Generating comments...")
            raw = create_comments(caption, niche, categories, language_distribution)
            lines = [line.strip() for line in raw.split("\n") if line.strip()]
            lines = split_broken_lines(lines)
            lines = remove_mentions(lines)
            lines = [clean_symbols(line) for line in lines]
            lines = clean_comments(lines)
            lines = remove_batch_numbering(lines)
            lines = remove_similar(lines)
            random.shuffle(lines)
            lines = enforce_count(lines, total_comments)

            # =================================
            # SAVE COMMENTS
            # =================================

            if not lines:
                raise RuntimeError("No valid comments remained after cleaning; post status was not updated.")

            save_comments(username,shortcode,lines)

            # =================================
            # UPDATE STATUS IMMEDIATELY
            # =================================

            post["ai_comments_generated"] = True
            generated_count += 1
            save_posts_json(path,posts)
            print(f"✅ Saved " f"{len(lines)} comments")

        except Exception as e:
            print(f"[ERROR] " f"{shortcode}: {e}")


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