def convert_to_discord_user(discord_user):
    if discord_user.__str__()[:2] != "<@":
        return f"<@{discord_user}>"
    else:
        return discord_user


class StringHelper:
    pass
