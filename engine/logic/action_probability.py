import random

# -------------------------
# PROBABILITY PROFILES (%)
# -------------------------

DEMO_PROBABILITY = {
    "like": 100,
    "comment": 35,
    "save": 50,
    "share": 100,
    "repost": 25,
}

PAID_PROBABILITY = {
    "like": 100,
    "comment": 100,
    "save": 100,
    "share": 100,
    "repost": 100,
}


# -------------------------
# DECISION FUNCTION
# -------------------------
def should_perform(action, probability_map):
    chance = probability_map.get(action, 100)

    roll = random.randint(1, 100)
    return roll <= chance
