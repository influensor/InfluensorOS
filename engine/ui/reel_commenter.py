import random
from engine.ui.comment import post_comment

PROMO_COMMENTS = [
    "This is insane growth! 🔥",
    "Content going viral for sure! 🚀",
    "Engagement level is next level! 💯",
    "This deserves more reach! 👀",
    "Algorithm gonna push this hard! ⚡",
    "Who else noticed this blowing up? 🔥",
    "Massive reach incoming! 💥",
    "Growth like this is rare! 📈",
    "This is insane growth! 🔥",
    "This gonna blow up! 🚀",
    "Engagement next level! 💯",
    "Growth on another level! 📈",
]

CTA_LINES = [
    "👉 Check @influensor.in",
    "🚀 Powered by @influensor.in",
    "📲 Growth by @influensor.in",
    "🔥 via @influensor.in",
    "⚡ See this @influensor.in",
    "👉 @influensor.in",
]

def generate_comment():
    base = random.choice(PROMO_COMMENTS)
    cta = random.choice(CTA_LINES)

    styles = [
        f"{base}\n{cta}",
        f"{cta}\n{base}",
    ]

    return random.choice(styles)

def reel_commenter(device_id):
    comment = generate_comment()
    return post_comment(device_id, comment)
