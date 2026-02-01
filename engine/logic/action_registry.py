def build(customer):
    actions = []
    settings = customer.get("settings", {})

    for key in ["like", "comment", "save", "share", "repost"]:
        if settings.get(key):
            actions.append(key)

    if settings.get("share_to_story"):
        actions.append("share_to_story")

    return actions
