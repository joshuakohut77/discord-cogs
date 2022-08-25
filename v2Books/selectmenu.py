from __future__ import annotations
from typing import Optional

import json

from discord import ActionRow, SelectMenu, SelectOption

class Select(ActionRow):
    def __init__(self, data: dict, *components) -> None:
        self.data: Optional[dict] = data
        super().__init__(*components)

    @classmethod
    def create(cls) -> ActionR:
        with open("books.json", "r") as data:
            data = json.load(data)
        
        options: list[SelectOption] = []
        for selector in data:
            options.append(SelectOption(label=selector, value=selector))
        
        return cls(data, SelectMenu(custom_id="bookselector", options=options))