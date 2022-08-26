from __future__ import annotations
from typing import Optional
import os
import sys
import json

from discord import ActionRow, SelectMenu, SelectOption

class Select(ActionRow):
    def __init__(self, data: dict, *components) -> None:
        self.data: Optional[dict] = data
        super().__init__(*components)

    @classmethod
    def create(cls) -> ActionR:
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'books.json.json')
        data = json.load(open(p, 'r'))
        # with open("books.json", "r") as data:
        #     data = json.load(data)
        
        options: list[SelectOption] = []
        for selector in data:
            options.append(SelectOption(label=selector, value=selector))
        
        return cls(data, SelectMenu(custom_id="bookselector", options=options))