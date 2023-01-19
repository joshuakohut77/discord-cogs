def convert_to_discord_user(discord_user: str):
    if discord_user[:2] != "<@":
        return f"<@{discord_user}>"
    else:
        return discord_user


class StringHelper:
    pass
