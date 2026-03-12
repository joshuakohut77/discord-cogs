"""
Pack opening engine for Pokemon TCG Collector.

Loads card metadata from cards.json, groups by set/rarity,
and simulates authentic WOTC era booster pack openings.
"""

import json
import os
import random
import logging
from typing import Optional

log = logging.getLogger("red.pokemontcg.packopener")


class CardPool:
    """
    Holds all card metadata grouped by set and rarity for fast pack generation.

    Rarity buckets per set:
        commons     - rarity == "Common"
        uncommons   - rarity == "Uncommon"
        rares_holo  - rarity == "Rare" and variants.holo == True
        rares_normal- rarity == "Rare" and variants.holo != True (or normal == True)
        energy      - category == "Energy"
        trainers    - category == "Trainer" (grouped by rarity as normal)
    """

    def __init__(self):
        self.cards_by_id: dict[str, dict] = {}
        self.sets: dict[str, dict] = {}  # set_id -> {commons, uncommons, rares_holo, rares_normal, energy}
        self.pack_config: dict = {}
        self.loaded = False

    def load(self, data_dir: str):
        """
        Load card data from the bulk downloader output.

        Args:
            data_dir: Path to the pokemon_cards directory containing cards.json and pack_config.json
        """
        cards_path = os.path.join(data_dir, "cards.json")
        config_path = os.path.join(data_dir, "pack_config.json")

        if not os.path.exists(cards_path):
            raise FileNotFoundError(f"Card data not found: {cards_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Pack config not found: {config_path}")

        # Load pack config
        with open(config_path, "r") as f:
            self.pack_config = json.load(f).get("sets", {})

        # Load card data
        with open(cards_path, "r") as f:
            master = json.load(f)

        all_cards = master.get("cards", [])
        log.info(f"Loading {len(all_cards)} cards from {cards_path}")

        # Index by ID
        for card in all_cards:
            card_id = card.get("id")
            if card_id:
                self.cards_by_id[card_id] = card

        # Group into rarity buckets per set
        for card in all_cards:
            set_id = card.get("set_id", "")
            if not set_id:
                continue

            if set_id not in self.sets:
                self.sets[set_id] = {
                    "commons": [],
                    "uncommons": [],
                    "rares_holo": [],
                    "rares_normal": [],
                    "energy": [],
                }

            pool = self.sets[set_id]
            category = (card.get("category") or "").lower()
            rarity = (card.get("rarity") or "").lower()
            is_holo = card.get("is_holo", False)
            is_normal = card.get("is_normal", False)

            # Energy cards go to their own bucket regardless of rarity
            if category == "energy":
                pool["energy"].append(card)
                continue

            # Sort into rarity buckets
            if rarity == "common":
                pool["commons"].append(card)
            elif rarity == "uncommon":
                pool["uncommons"].append(card)
            elif "rare" in rarity:
                # Cards can exist in both holo and normal pools
                # if they were printed as both variants
                if is_holo:
                    pool["rares_holo"].append(card)
                if is_normal or not is_holo:
                    pool["rares_normal"].append(card)
            elif not rarity or rarity == "none":
                # Cards with no rarity (some energy/trainers) - treat as common
                pool["commons"].append(card)

        # Log pool sizes
        for set_id, pool in self.sets.items():
            config = self.pack_config.get(set_id, {})
            name = config.get("name", set_id)
            log.info(
                f"  {name}: {len(pool['commons'])}C / {len(pool['uncommons'])}U / "
                f"{len(pool['rares_holo'])}RH / {len(pool['rares_normal'])}R / "
                f"{len(pool['energy'])}E"
            )

        self.loaded = True

    def get_available_sets(self) -> list[dict]:
        """Return list of sets that have both card data and pack config."""
        available = []
        for set_id, config in self.pack_config.items():
            if set_id in self.sets:
                pool = self.sets[set_id]
                total = sum(len(v) for v in pool.values())
                available.append({
                    "set_id": set_id,
                    "name": config.get("name", set_id),
                    "emoji": config.get("emoji", "📦"),
                    "description": config.get("description", ""),
                    "year": config.get("year", 0),
                    "total_in_set": config.get("total_cards_in_set", total),
                    "cards_per_pack": config.get("cards_per_pack", 11),
                })
        return sorted(available, key=lambda s: (s["year"], s["set_id"]))

    def open_pack(self, set_id: str) -> Optional[list[dict]]:
        """
        Simulate opening a booster pack from the given set.

        Returns a list of card dicts representing the pulled cards,
        or None if the set is invalid/unavailable.

        Each card dict is a copy of the metadata with an added 'pulled_as_holo'
        field indicating whether this specific pull is the holo variant.
        """
        if set_id not in self.sets or set_id not in self.pack_config:
            return None

        pool = self.sets[set_id]
        config = self.pack_config[set_id]
        composition = config.get("pack_composition", {})
        holo_chance = config.get("holo_chance", 0.333)

        pulled_cards = []

        # 1. Rare slot (1 card) — roll for holo
        is_holo_pull = random.random() < holo_chance

        if is_holo_pull and pool["rares_holo"]:
            rare = random.choice(pool["rares_holo"])
            pulled_cards.append(self._make_pull(rare, pulled_as_holo=True))
        elif pool["rares_normal"]:
            rare = random.choice(pool["rares_normal"])
            pulled_cards.append(self._make_pull(rare, pulled_as_holo=False))
        elif pool["rares_holo"]:
            # Fallback: no normal rares, use holo anyway
            rare = random.choice(pool["rares_holo"])
            pulled_cards.append(self._make_pull(rare, pulled_as_holo=True))

        # 2. Uncommon slots
        num_uncommon = composition.get("uncommon", 3)
        if pool["uncommons"]:
            for _ in range(num_uncommon):
                card = random.choice(pool["uncommons"])
                pulled_cards.append(self._make_pull(card, pulled_as_holo=False))

        # 3. Common slots
        num_common = composition.get("common", 5)
        if pool["commons"]:
            for _ in range(num_common):
                card = random.choice(pool["commons"])
                pulled_cards.append(self._make_pull(card, pulled_as_holo=False))

        # 4. Energy slots (if applicable)
        num_energy = composition.get("energy", 0)
        if num_energy > 0 and pool["energy"]:
            for _ in range(num_energy):
                card = random.choice(pool["energy"])
                pulled_cards.append(self._make_pull(card, pulled_as_holo=False))

        return pulled_cards

    @staticmethod
    def _make_pull(card: dict, pulled_as_holo: bool) -> dict:
        """Create a pull result dict from a card, adding pull-specific fields."""
        return {
            "id": card.get("id"),
            "local_id": card.get("local_id"),
            "name": card.get("name"),
            "set_id": card.get("set_id"),
            "set_name": card.get("set_name"),
            "category": card.get("category"),
            "rarity": card.get("rarity"),
            "hp": card.get("hp"),
            "types": card.get("types", []),
            "stage": card.get("stage"),
            "attacks": card.get("attacks", []),
            "weaknesses": card.get("weaknesses", []),
            "resistances": card.get("resistances", []),
            "abilities": card.get("abilities", []),
            "retreat": card.get("retreat"),
            "illustrator": card.get("illustrator"),
            "image_high": card.get("image_high"),
            "image_low": card.get("image_low"),
            "image_file": card.get("image_file"),
            "effect": card.get("effect"),
            "description": card.get("description"),
            # Pull-specific
            "pulled_as_holo": pulled_as_holo,
            "is_holo": card.get("is_holo", False),
            "is_normal": card.get("is_normal", False),
        }