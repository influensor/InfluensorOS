def build(customer):
    actions = []
    settings = customer.get("settings", {})

    for key in [
        "like",
        "comment",
        "gif_comment",
        "save",
        "share",
        "repost",
        "interested",
        "add_to_story",
    ]:
        if settings.get(key):
            actions.append(key)

    return actions
