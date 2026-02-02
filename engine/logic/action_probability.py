import random

# -------------------------
# PROBABILITY PROFILES (%)
# -------------------------

DEMO_PROBABILITY = {
    "like": 100,
    "comment": 60,
    "save": 50,
    "share": 35,
    "repost": 25,
}

PAID_PROBABILITY = {
    "like": 100,
    "comment": 60,
    "save": 50,
    "share": 35,
    "repost": 25,
}


# -------------------------
# DECISION FUNCTION
# -------------------------
def should_perform(action, probability_map):
    chance = probability_map.get(action, 100)

    roll = random.randint(1, 100)
    return roll <= chance
