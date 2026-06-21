import random

# -------------------------
# PROBABILITY PROFILES (%)
# -------------------------

DEMO_PROBABILITY = {
    "like": 100,
    "comment": 60,
    "gif_comment": 5,
    "repost": 30,
    "share": 60,
    "save": 40,
    "interested": 70,
    "add_to_story": 60,
}

PAID_PROBABILITY = {
    "like": 100,
    "comment": 40,
    "gif_comment": 5,
    "repost": 20,
    "share": 50,
    "save": 40,
    "interested": 60,
    "add_to_story": 0,
}


# -------------------------
# DECISION FUNCTION
# -------------------------
def should_perform(action, probability_map):
    chance = probability_map.get(action, 100)

    roll = random.randint(1, 100)
    return roll <= chance
