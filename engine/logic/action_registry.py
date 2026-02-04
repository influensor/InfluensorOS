def build(customer):
    actions = []
    settings = customer.get("settings", {})

    for key in ["like", "comment", "save", "share", "repost"]:
        if settings.get(key):
            actions.append(key)
    return actions
