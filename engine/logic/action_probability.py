import random

# -------------------------
# PROBABILITY PROFILES (%)
# -------------------------

DEMO_PROBABILITY = {
    "like": 100,
    "comment": 60,
    "gif_comment": 25,
    "repost": 60,
    "share": 100,
    "save": 60,
    "interested": 100,
    "add_to_story": 60,
}

PAID_PROBABILITY = {
    "like": 100,
    "comment": 35,
    "gif_comment": 5,
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
