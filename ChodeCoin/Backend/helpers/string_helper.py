import re


def convert_to_discord_user(target_user):
    user_name_check = re.search(r"\d{18,20}", target_user.__str__())
    if user_name_check:
        if target_user.__str__()[:2] != "<@":
            return f"<@{target_user}"
        else:
            return target_user
    else:
        return target_user


class StringHelper:
    pass
