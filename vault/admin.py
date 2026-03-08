from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import logging

import discord
from redbot.core import commands
from .abc import MixinMeta
from .db import VaultDB
from .constants import EMBED_COLOR, STORE_EMBED_COLOR, COIN_EMOJI, ALL_CATEGORIES

if TYPE_CHECKING:
    pass

log = logging.getLogger("red.vault.admin")


class AdminMixin(MixinMeta):
    """Admin commands for Vault card and store management."""

    __slots__: tuple = ()

    @commands.group(name="vaultadmin", aliases=["va"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def vaultadmin(self, ctx: commands.Context):
        """Admin commands for managing The Vault."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # ------------------------------------------------------------------
    # Store config
    # ------------------------------------------------------------------

    @vaultadmin.command(name="setprice")
    async def set_price(self, ctx: commands.Context, category: str, price: int):
        """Set the pull price for a category.

        Example: `[p]va setprice item 2`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            categories = ", ".join(f"`{c}`" for c in ALL_CATEGORIES)
            return await ctx.send(f"Invalid category. Options: {categories}")
        if price < 0:
            return await ctx.send("Price can't be negative.")

        await asyncio.to_thread(VaultDB.set_store_price, ctx.guild.id, category, price)
        await ctx.send(f"Pull price for **{category}** set to **{price}** {COIN_EMOJI}.")

    @vaultadmin.command(name="opencat")
    async def open_category(self, ctx: commands.Context, category: str):
        """Open a category in the store.

        Example: `[p]va opencat weapon`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            return await ctx.send(f"Invalid category.")

        await asyncio.to_thread(VaultDB.set_store_open, ctx.guild.id, category, True)
        await ctx.send(f"**{category.title()}** is now open in the store.")

    @vaultadmin.command(name="closecat")
    async def close_category(self, ctx: commands.Context, category: str):
        """Close a category in the store (players can't buy from it).

        Example: `[p]va closecat weapon`
        """
        category = category.lower()
        if category not in ALL_CATEGORIES:
            return await ctx.send(f"Invalid category.")

        await asyncio.to_thread(VaultDB.set_store_open, ctx.guild.id, category, False)
        await ctx.send(f"**{category.title()}** is now closed in the store.")

    @vaultadmin.command(name="storeconfig")
    async def store_config(self, ctx: commands.Context):
        """View current store configuration for this server."""
        config = await asyncio.to_thread(VaultDB.get_all_store_config, ctx.guild.id)

        embed = discord.Embed(
            title="Store Configuration",
            color=STORE_EMBED_COLOR,
        )

        for cat in ALL_CATEGORIES:
            cfg = config.get(cat, {"pull_price": 5, "is_open": True})
            status = "\u2705 Open" if cfg["is_open"] else "\u274c Closed"
            embed.add_field(
                name=cat.title(),
                value=f"Price: **{cfg['pull_price']}** {COIN_EMOJI}\nStatus: {status}",
                inline=True,
            )

        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Card management
    # ------------------------------------------------------------------

    @vaultadmin.command(name="addcard")
    async def add_card(
        self,
        ctx: commands.Context,
        category: str,
        rarity: str,
        name: str,
        *,
        text: str,
    ):
        """Add a card to the catalog.

        The text should have the explanation and blurb separated by `|`.

        Example: `[p]va addcard item common Healing Potion Restores a small amount of health. | A simple glass vial filled with a glowing red liquid. One sip mends minor wounds, but don't expect miracles.`
        """
        category = category.lower()
        rarity = rarity.lower()

        if category not in ALL_CATEGORIES:
            categories = ", ".join(f"`{c}`" for c in ALL_CATEGORIES)
            return await ctx.send(f"Invalid category. Options: {categories}")

        valid_rarities = ["common", "uncommon", "rare", "legendary"]
        if rarity not in valid_rarities:
            return await ctx.send(f"Invalid rarity. Options: {', '.join(valid_rarities)}")

        parts = text.split("|", 1)
        if len(parts) != 2:
            return await ctx.send("Separate the explanation and blurb with `|`.\nExample: `Short description. | Longer detailed blurb.`")

        explanation = parts[0].strip()
        blurb = parts[1].strip()

        card_id = await asyncio.to_thread(
            VaultDB.add_card, name, category, rarity, explanation, blurb
        )

        embed = discord.Embed(
            title=f"Card Added — #{card_id}",
            description=f"**{name}**\n{category.title()} / {rarity.title()}",
            color=EMBED_COLOR,
        )
        embed.add_field(name="Explanation", value=explanation, inline=False)
        embed.add_field(name="Blurb", value=blurb, inline=False)
        embed.set_footer(text=f"Use `{ctx.prefix}va setprop {card_id} <key> <value>` to add properties")
        await ctx.send(embed=embed)

    @vaultadmin.command(name="setprop")
    async def set_prop(self, ctx: commands.Context, card_id: int, key: str, *, value: str):
        """Set a property on a card.

        Example: `[p]va setprop 1 consumable true`
        Example: `[p]va setprop 1 max_uses 3`
        """
        card = await asyncio.to_thread(VaultDB.get_card, card_id)
        if not card:
            return await ctx.send(f"No card found with ID **{card_id}**.")

        await asyncio.to_thread(VaultDB.set_card_property, card_id, key, value)
        await ctx.send(f"Set `{key}` = `{value}` on **{card['name']}** (#{card_id}).")

    @vaultadmin.command(name="delprop")
    async def del_prop(self, ctx: commands.Context, card_id: int, key: str):
        """Remove a property from a card.

        Example: `[p]va delprop 1 seasonal`
        """
        card = await asyncio.to_thread(VaultDB.get_card, card_id)
        if not card:
            return await ctx.send(f"No card found with ID **{card_id}**.")

        await asyncio.to_thread(VaultDB.remove_card_property, card_id, key)
        await ctx.send(f"Removed `{key}` from **{card['name']}** (#{card_id}).")

    @vaultadmin.command(name="listcards")
    async def list_cards(self, ctx: commands.Context, category: str = None, rarity: str = None):
        """List cards in the catalog.

        Example: `[p]va listcards` or `[p]va listcards weapon rare`
        """
        if category:
            category = category.lower()
        if rarity:
            rarity = rarity.lower()

        cards = await asyncio.to_thread(VaultDB.browse_store, category, rarity, limit=50)

        if not cards:
            return await ctx.send("No cards found matching those filters.")

        lines = []
        for card in cards:
            lines.append(
                f"`#{card['id']}` **{card['name']}** — {card['category'].title()} / {card['rarity'].title()}"
            )

        embed = discord.Embed(
            title="Card Catalog",
            description="\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text=f"{len(cards)} cards shown")
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Grant / Revoke
    # ------------------------------------------------------------------

    @vaultadmin.command(name="grant")
    async def grant(self, ctx: commands.Context, member: discord.Member, card_id: int):
        """Grant a card to a player (no CC cost).

        Example: `[p]va grant @User 5`
        """
        card = await asyncio.to_thread(VaultDB.get_card, card_id)
        if not card:
            return await ctx.send(f"No card found with ID **{card_id}**.")

        inv_id = await asyncio.to_thread(
            VaultDB.grant_card, ctx.guild.id, member.id, card_id, "admin"
        )
        await ctx.send(
            f"Granted **{card['name']}** to {member.mention}. (Inventory ID: {inv_id})"
        )

    @vaultadmin.command(name="revoke")
    async def revoke(self, ctx: commands.Context, inv_id: int):
        """Revoke (retire) a card from a player's inventory by inventory ID.

        Example: `[p]va revoke 42`
        """
        item = await asyncio.to_thread(VaultDB.get_inventory_item, inv_id)
        if not item:
            return await ctx.send(f"No inventory item found with ID **{inv_id}**.")

        await asyncio.to_thread(VaultDB.retire_item, inv_id)
        await ctx.send(f"Revoked **{item['name']}** (inv #{inv_id}) from <@{item['user_id']}>.")