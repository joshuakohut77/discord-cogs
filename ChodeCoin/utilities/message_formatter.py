import json
import re
import discord
import json
from discord import embeds


class MessageFormatter:

    def extract_targeted_user(self, message, process):
        targeted_user = ""

        if process == "PlusPlus":
            targeted_user = re.search("@.{2,32}?[+]{2}", message)
        elif process == "MinusMinus":
            targeted_user = re.search("@.{2,32}?-{2}", message)
        else:
            raise NameError("Process not defined")

        formatted_user = targeted_user[:len(str(targeted_user))-2].strip()
        return formatted_user
