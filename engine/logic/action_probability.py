import random

# -------------------------
# PROBABILITY PROFILES (%)
# -------------------------

DEMO_PROBABILITY = {
    "like": 100,
    "comment": 35,
    "gif_comment": 15,
    "repost": 45,
    "share": 100,
    "save": 55,
    "interested": 100,
    "add_to_story": 40,
}

PAID_PROBABILITY = {
    "like": 100,
    "comment": 35,
    "gif_comment": 15,
    "repost": 45,
    "share": 100,
    "save": 55,
    "interested": 100,
    "add_to_story": 0,
}


# -------------------------
# DECISION FUNCTION
# -------------------------
def should_perform(action, probability_map):
    chance = probability_map.get(action, 100)

    roll = random.randint(1, 100)
    return roll <= chance
