# pokemon/trade.py
from __future__ import annotations
from typing import Any, Dict, List, Union, TYPE_CHECKING, Optional

import discord
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, View, Select

from redbot.core.commands.context import Context

if TYPE_CHECKING:
    from redbot.core.bot import Red

from redbot.core import commands

from services.trainerclass import trainer as TrainerClass
from services.pokeclass import Pokemon as PokemonClass
from services.encounterclass import encounter as EncounterClass
from services.traderequestclass import TradeRequest

from .abcd import MixinMeta
from .functions import createStatsEmbed


class TradeMixin(MixinMeta):
    """Async Pokemon Trading System"""
    
    def __init__(self):
        super().__init__()
        self.trade_service = TradeRequest()
    
    # ==================== PC Integration ====================
    
    def get_trade_button_for_pc(self, user_id: str) -> tuple[Button, Optional[int]]:
        """
        Returns (button, trade_id) for PC menu.
        Button changes based on trade state.
        """
        trade = self.trade_service.get_active_trade(user_id)
        
        # DEBUG
        print(f"[TRADE DEBUG] get_trade_button_for_pc called for user {user_id}")
        print(f"[TRADE DEBUG] Active trade found: {trade is not None}")
        if trade:
            print(f"[TRADE DEBUG] Trade ID: {trade['trade_id']}, Status: {trade['status']}")
            print(f"[TRADE DEBUG] Sender: {trade['sender_discord_id']}, Receiver: {trade['receiver_discord_id']}")
        
        if not trade:
            # No active trade - show normal Trade button
            button = Button(style=ButtonStyle.green, label="Trade", custom_id='trade_initiate')
            button.callback = self._on_trade_initiate
            return button, None
        
        trade_id = trade['trade_id']
        
        # Receiver needs to respond
        if (trade['status'] == TradeRequest.STATUS_PENDING_RECEIVER and 
            trade['receiver_discord_id'] == user_id):
            print(f"[TRADE DEBUG] Returning 'View Trade Request' button for receiver")
            button = Button(style=ButtonStyle.blurple, label="View Trade Request", custom_id=f'view_request_{trade_id}')
            button.callback = self._on_view_request_receiver
            return button, trade_id
        
        # Sender needs to accept counter-offer
        if (trade['status'] == TradeRequest.STATUS_PENDING_SENDER and 
            trade['sender_discord_id'] == user_id):
            print(f"[TRADE DEBUG] Returning 'View Trade Response' button for sender")
            button = Button(style=ButtonStyle.blurple, label="View Trade Response", custom_id=f'view_response_{trade_id}')
            button.callback = self._on_view_response_sender
            return button, trade_id
        
        # Waiting on other person
        print(f"[TRADE DEBUG] Returning 'Trade Pending...' button (waiting on other person)")
        button = Button(style=ButtonStyle.gray, label="Trade Pending...", custom_id='trade_pending', disabled=True)
        return button, trade_id
    
    # ==================== Step 1: Initiate Trade ====================
    
    async def _on_trade_initiate(self, interaction: Interaction):
        """Step 1: User clicks Trade button in PC"""
        user = interaction.user
        await interaction.response.defer()
        
        # Check if user has a Link Cable
        from services.inventoryclass import inventory as InventoryClass
        inv = InventoryClass(str(user.id))
        if inv.linkcable < 1:
            await interaction.followup.send(
                "🔗 You need a **Link Cable** to trade! Visit a Poké Mart to buy one.",
                ephemeral=True
            )
            return
        
        # Check if user already has active trade
        if self.trade_service.has_active_trade(str(user.id)):
            await interaction.followup.send(
                "You already have an active trade request. Please complete or cancel it first."
            )
            return
        
        # Get guild from the message's channel
        if not interaction.message or not interaction.message.guild:
            await interaction.followup.send(
                "Error: This command must be used in a server channel."
            )
            return
        
        guild = interaction.message.guild
        
        # Get list of online guild members (excluding self and bots)
        online_members = [
            m for m in guild.members 
            if not m.bot 
            and m.id != user.id 
            and m.status != discord.Status.offline
        ]
        
        if not online_members:
            await interaction.followup.send(
                "No other users are currently online to trade with."
            )
            return
        
        # Get user's Pokemon (excluding active)
        trainer = TrainerClass(str(user.id))
        active_pokemon = trainer.getActivePokemon()
        all_pokemon = trainer.getPokemon(False, True)  # party=False, pc=True gets all
        
        # LOAD each Pokemon's data
        for p in all_pokemon:
            p.load(pokemonId=p.trainerId)
        
        tradeable_pokemon = [p for p in all_pokemon if p.trainerId != active_pokemon.trainerId]
        
        if not tradeable_pokemon:
            await interaction.followup.send(
                "You don't have any Pokemon available to trade (excluding your active Pokemon)."
            )
            return
        
        # Create the selection view
        view = TradeInitiateView(user, online_members, tradeable_pokemon, self)
        
        embed = discord.Embed(
            title="🔄 Initiate Trade",
            description="Select a user and Pokemon to start a trade request.",
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed, view=view)


    # ==================== Step 2: Receiver Views Request ====================
    
    async def _on_view_request_receiver(self, interaction: Interaction):
        """Step 2: Receiver views incoming trade request"""
        user = interaction.user
        await interaction.response.defer()
        
        trade = self.trade_service.get_active_trade(str(user.id))
        if not trade:
            await interaction.followup.send("Trade request not found.")
            return
        
        if trade['receiver_discord_id'] != str(user.id):
            await interaction.followup.send("This trade request is not for you.")
            return
        
        # Get sender's info
        sender = await self.bot.fetch_user(int(trade['sender_discord_id']))
        
        # Create embed showing offered Pokemon
        pokemon_name = trade['sender_pokemon_nickname'] or trade['sender_pokemon_name']
        
        embed = discord.Embed(
            title="📬 Trade Request",
            description=f"**{sender.display_name}** wants to trade with you!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Offering",
            value=f"**{pokemon_name}** ({trade['sender_pokemon_name']})\nLevel {trade['sender_pokemon_level']}",
            inline=False
        )
        
        if trade['sender_type_2']:
            types = f"{trade['sender_type_1']}/{trade['sender_type_2']}"
        else:
            types = trade['sender_type_1']
        embed.add_field(name="Type", value=types, inline=True)
        
        # Add Pokemon sprite as file attachment
        sprite_file = None
        try:
            import os
            from helpers.pathhelpers import get_sprite_path
            
            sprite_path = f"/sprites/pokemon/{trade['sender_pokemon_name']}.png"
            full_sprite_path = get_sprite_path(sprite_path)
            
            if os.path.exists(full_sprite_path):
                filename = f"{trade['sender_pokemon_name']}.png"
                sprite_file = discord.File(full_sprite_path, filename=filename)
                embed.set_thumbnail(url=f"attachment://{filename}")
        except Exception as e:
            # Sprite loading failed, continue without sprite
            pass
        
        # Create accept/decline view
        view = TradeReceiverResponseView(user, trade['trade_id'], self)
        
        # Send with or without sprite - REMOVED ephemeral=True
        if sprite_file:
            await interaction.followup.send(embed=embed, view=view, file=sprite_file)
        else:
            await interaction.followup.send(embed=embed, view=view)

    # ==================== Step 3: Sender Views Counter-Offer ====================
    
    async def _on_view_response_sender(self, interaction: Interaction):
        """Step 3: Sender views receiver's counter-offer"""
        user = interaction.user
        await interaction.response.defer()
        
        trade = self.trade_service.get_active_trade(str(user.id))
        if not trade:
            await interaction.followup.send("Trade request not found.", ephemeral=True)
            return
        
        if trade['sender_discord_id'] != str(user.id):
            await interaction.followup.send("This trade request is not yours.", ephemeral=True)
            return
        
        # Get receiver's info
        receiver = await self.bot.fetch_user(int(trade['receiver_discord_id']))
        
        # Create embed showing both Pokemon
        embed = discord.Embed(
            title="🔄 Trade Response",
            description=f"**{receiver.display_name}** has responded to your trade!",
            color=discord.Color.green()
        )
        
        # Your Pokemon
        your_pokemon_name = trade['sender_pokemon_nickname'] or trade['sender_pokemon_name']
        embed.add_field(
            name="You're Trading",
            value=f"**{your_pokemon_name}** ({trade['sender_pokemon_name']})\nLevel {trade['sender_pokemon_level']}",
            inline=True
        )
        
        # Their Pokemon
        their_pokemon_name = trade['receiver_pokemon_nickname'] or trade['receiver_pokemon_name']
        embed.add_field(
            name="For Their",
            value=f"**{their_pokemon_name}** ({trade['receiver_pokemon_name']})\nLevel {trade['receiver_pokemon_level']}",
            inline=True
        )
        
        # Create accept/decline view
        view = TradeSenderAcceptView(user, trade['trade_id'], self)
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    # ==================== Trade Execution ====================
    
    async def execute_trade(self, trade_id: int) -> tuple[bool, str]:
        """
        Execute the actual Pokemon trade.
        Returns (success, message)
        """
        # Validate trade can be executed
        is_valid, error_msg = self.trade_service.validate_trade_execution(trade_id)
        if not is_valid:
            self.trade_service.invalidate_trade(trade_id)
            return False, error_msg
        
        # Get trade details
        trade = self.trade_service.get_trade_by_id(trade_id)
        
        # Load both Pokemon - need to pass discordId to constructor
        sender_pokemon = PokemonClass(trade['sender_discord_id'])
        sender_pokemon.load(pokemonId=trade['sender_pokemon_id'])
        
        receiver_pokemon = PokemonClass(trade['receiver_discord_id'])
        receiver_pokemon.load(pokemonId=trade['receiver_pokemon_id'])
        
        # Execute trade via EncounterClass (handles evolution, pokedex, leaderboard)
        enc = EncounterClass(sender_pokemon, receiver_pokemon)
        retVal1, retVal2 = enc.trade()
        
        # Get evolution info from the encounter
        evo_info = getattr(enc, 'trade_evolution_info', {})
        
        # NOTE: Pokedex registration is now handled inside enc.trade()
        # so we no longer need to do it here
        
        # Mark trade as completed
        self.trade_service.complete_trade(trade_id)
        
        # Send DMs to both users
        try:
            import os
            from helpers.pathhelpers import get_sprite_path
            
            sender = await self.bot.fetch_user(int(trade['sender_discord_id']))
            receiver = await self.bot.fetch_user(int(trade['receiver_discord_id']))
            
            # ---- DM to SENDER ----
            # Sender receives pokemon2 (the receiver's original pokemon)
            # Check if pokemon2 evolved (that's what sender receives)
            p2_evolved = evo_info.get('pokemon2_evolved', False)
            p2_original = evo_info.get('pokemon2_original', None)
            p2_evolved_into = evo_info.get('pokemon2_evolved_into', None)
            
            sender_embed = discord.Embed(
                title="✅ Trade Complete!",
                description=f"Your trade with **{receiver.display_name}** is complete!",
                color=discord.Color.green()
            )
            
            if p2_evolved:
                # The pokemon they received evolved!
                sender_embed.add_field(
                    name="You Received",
                    value=f"**{trade['receiver_pokemon_name'].capitalize()}** (Level {trade['receiver_pokemon_level']})",
                    inline=False
                )
                sender_embed.add_field(
                    name="✨ What's this?!",
                    value=f"**{p2_original.capitalize()}** evolved into **{p2_evolved_into.capitalize()}**!",
                    inline=False
                )
                # Use evolved pokemon's sprite
                sprite_pokemon_name = p2_evolved_into
            else:
                sender_embed.add_field(
                    name="You Received",
                    value=f"**{trade['receiver_pokemon_name'].capitalize()}** (Level {trade['receiver_pokemon_level']})",
                    inline=False
                )
                sprite_pokemon_name = trade['receiver_pokemon_name']
            
            # Add sprite
            sender_sprite_file = None
            try:
                sprite_path = f"/sprites/pokemon/{sprite_pokemon_name}.png"
                full_sprite_path = get_sprite_path(sprite_path)
                
                if os.path.exists(full_sprite_path):
                    filename = f"{sprite_pokemon_name}.png"
                    sender_sprite_file = discord.File(full_sprite_path, filename=filename)
                    sender_embed.set_thumbnail(url=f"attachment://{filename}")
            except Exception as e:
                pass
            
            if sender_sprite_file:
                await sender.send(embed=sender_embed, file=sender_sprite_file)
            else:
                await sender.send(embed=sender_embed)
            
            # ---- DM to RECEIVER ----
            # Receiver receives pokemon1 (the sender's original pokemon)
            # Check if pokemon1 evolved (that's what receiver gets)
            p1_evolved = evo_info.get('pokemon1_evolved', False)
            p1_original = evo_info.get('pokemon1_original', None)
            p1_evolved_into = evo_info.get('pokemon1_evolved_into', None)
            
            receiver_embed = discord.Embed(
                title="✅ Trade Complete!",
                description=f"Your trade with **{sender.display_name}** is complete!",
                color=discord.Color.green()
            )
            
            if p1_evolved:
                # The pokemon they received evolved!
                receiver_embed.add_field(
                    name="You Received",
                    value=f"**{trade['sender_pokemon_name'].capitalize()}** (Level {trade['sender_pokemon_level']})",
                    inline=False
                )
                receiver_embed.add_field(
                    name="✨ What's this?!",
                    value=f"**{p1_original.capitalize()}** evolved into **{p1_evolved_into.capitalize()}**!",
                    inline=False
                )
                # Use evolved pokemon's sprite
                sprite_pokemon_name = p1_evolved_into
            else:
                receiver_embed.add_field(
                    name="You Received",
                    value=f"**{trade['sender_pokemon_name'].capitalize()}** (Level {trade['sender_pokemon_level']})",
                    inline=False
                )
                sprite_pokemon_name = trade['sender_pokemon_name']
            
            # Add sprite
            receiver_sprite_file = None
            try:
                sprite_path = f"/sprites/pokemon/{sprite_pokemon_name}.png"
                full_sprite_path = get_sprite_path(sprite_path)
                
                if os.path.exists(full_sprite_path):
                    filename = f"{sprite_pokemon_name}.png"
                    receiver_sprite_file = discord.File(full_sprite_path, filename=filename)
                    receiver_embed.set_thumbnail(url=f"attachment://{filename}")
            except Exception as e:
                pass
            
            if receiver_sprite_file:
                await receiver.send(embed=receiver_embed, file=receiver_sprite_file)
            else:
                await receiver.send(embed=receiver_embed)
            
        except discord.Forbidden:
            pass  # User has DMs disabled
        except Exception as e:
            print(f"Error sending trade completion DMs: {e}")
        
        return True, "Trade completed successfully!"

    async def cancel_trade_notify(self, trade_id: int, cancelled_by_discord_id: str):
        """Cancel trade and notify both users"""
        trade = self.trade_service.get_trade_by_id(trade_id)
        if not trade:
            return
        
        # Cancel in database
        self.trade_service.cancel_trade(trade_id, cancelled_by_discord_id)
        
        # Determine who cancelled
        canceller = await self.bot.fetch_user(int(cancelled_by_discord_id))
        
        if cancelled_by_discord_id == trade['sender_discord_id']:
            other_user_id = trade['receiver_discord_id']
        else:
            other_user_id = trade['sender_discord_id']
        
        other_user = await self.bot.fetch_user(int(other_user_id))
        
        # Send DMs
        try:
            cancel_embed = discord.Embed(
                title="❌ Trade Cancelled",
                description=f"**{canceller.display_name}** has cancelled the trade request.",
                color=discord.Color.red()
            )
            
            await canceller.send("You cancelled the trade request.")
            await other_user.send(embed=cancel_embed)
            
        except discord.Forbidden:
            pass  # User has DMs disabled
        except Exception as e:
            print(f"Error sending cancellation DMs: {e}")
    
    # ==================== Commands ====================
    
    @commands.group(name="pokecenter", aliases=['pmc'])
    @commands.guild_only()
    async def _pokecenter(self, ctx: commands.Context) -> None:
        """Base command to manage the pokecenter"""
        pass
    
    @_pokecenter.command()
    async def tradehistory(self, ctx: commands.Context, limit: int = 10):
        """View your recent completed trades"""
        user = ctx.author
        
        if limit > 20:
            limit = 20
        
        trades = self.trade_service.get_trade_history(str(user.id), limit)
        
        if not trades:
            await ctx.send("You haven't completed any trades yet.")
            return
        
        embed = discord.Embed(
            title=f"📜 {user.display_name}'s Trade History",
            description=f"Your last {len(trades)} completed trades:",
            color=discord.Color.blue()
        )
        
        for trade in trades:
            # Determine which Pokemon the user gave/received
            if trade['sender_discord_id'] == str(user.id):
                gave = trade['sender_pokemon_name']
                received = trade['receiver_pokemon_name']
                partner_id = trade['receiver_discord_id']
            else:
                gave = trade['receiver_pokemon_name']
                received = trade['sender_pokemon_name']
                partner_id = trade['sender_discord_id']
            
            try:
                partner = await self.bot.fetch_user(int(partner_id))
                partner_name = partner.display_name
            except:
                partner_name = "Unknown User"
            
            completed = trade['completed_at'].strftime('%Y-%m-%d %H:%M')
            
            embed.add_field(
                name=f"Trade with {partner_name}",
                value=f"Gave: **{gave}**\nReceived: **{received}**\n{completed}",
                inline=False
            )
        
        await ctx.send(embed=embed)


# ==================== UI Views ====================

class TradeInitiateView(View):
    """View for selecting user and Pokemon to trade"""
    
    def __init__(self, user: discord.User, members: List[discord.Member], pokemon: List[PokemonClass], mixin: TradeMixin):
        super().__init__(timeout=180)
        self.user = user
        self.mixin = mixin
        self.members = members
        self.pokemon = pokemon
        self.selected_member: Optional[discord.Member] = None
        self.selected_pokemon: Optional[PokemonClass] = None
        
        self._build_view()
    
    def _build_view(self):
        """Build/rebuild the view with current selections"""
        self.clear_items()
        
        # User dropdown
        user_options = [
            SelectOption(
                label=m.display_name, 
                value=str(m.id), 
                description=f"Trade with {m.name}",
                default=(self.selected_member and m.id == self.selected_member.id)
            )
            for m in self.members[:25]  # Discord limit
        ]
        
        user_select = Select(
            placeholder="Select a user to trade with...",
            options=user_options,
            custom_id="user_select"
        )
        user_select.callback = self.user_selected
        self.add_item(user_select)
        
        # Pokemon dropdown
        pokemon_options = [
            SelectOption(
                label=f"{p.nickName or p.pokemonName} (Lv.{p.currentLevel})",
                value=str(p.trainerId),
                description=f"{p.pokemonName} - {p.type1}" + (f"/{p.type2}" if p.type2 else ""),
                default=(self.selected_pokemon and p.trainerId == self.selected_pokemon.trainerId)
            )
            for p in self.pokemon[:25]  # Discord limit
        ]
        
        pokemon_select = Select(
            placeholder="Select a Pokemon to offer...",
            options=pokemon_options,
            custom_id="pokemon_select"
        )
        pokemon_select.callback = self.pokemon_selected
        self.add_item(pokemon_select)
        
        # Send request button (disabled until both selections made)
        send_enabled = self.selected_member is not None and self.selected_pokemon is not None
        send_button = Button(
            label="Send Trade Request", 
            style=ButtonStyle.green, 
            custom_id="send_request", 
            disabled=not send_enabled
        )
        send_button.callback = self.send_request
        self.add_item(send_button)
        
        # Cancel button
        cancel_button = Button(label="Cancel", style=ButtonStyle.red, custom_id="cancel")
        cancel_button.callback = self.cancel
        self.add_item(cancel_button)
    
    async def user_selected(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        selected_id = int(interaction.data['values'][0])
        self.selected_member = interaction.guild.get_member(selected_id)
        
        # Rebuild view with new selection
        self._build_view()
        await interaction.message.edit(view=self)
    
    async def pokemon_selected(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        selected_id = int(interaction.data['values'][0])
        # Find the Pokemon in our list
        self.selected_pokemon = None
        for p in self.pokemon:
            if p.trainerId == selected_id:
                self.selected_pokemon = p
                break
        
        # Rebuild view with new selection
        self._build_view()
        await interaction.message.edit(view=self)
    
    async def send_request(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Create trade request in database
        trade_id = self.mixin.trade_service.create_trade_request(
            str(self.user.id),
            str(self.selected_member.id),
            self.selected_pokemon.trainerId
        )
        
        if not trade_id:
            error_msg = f"Failed to create trade request.\nError: {self.mixin.trade_service.message}"
            await interaction.followup.send(error_msg)
            return
        
        # Send DM to receiver
        try:
            import os
            from helpers.pathhelpers import get_sprite_path
            
            pokemon_name = self.selected_pokemon.nickName or self.selected_pokemon.pokemonName
            
            dm_embed = discord.Embed(
                title="📬 New Trade Request!",
                description=f"**{self.user.display_name}** wants to trade with you!",
                color=discord.Color.blue()
            )
            dm_embed.add_field(
                name="They're Offering",
                value=f"**{pokemon_name}** ({self.selected_pokemon.pokemonName})\nLevel {self.selected_pokemon.currentLevel}",
                inline=False
            )
            
            # Add type info
            type_str = self.selected_pokemon.type1
            if self.selected_pokemon.type2:
                type_str += f"/{self.selected_pokemon.type2}"
            dm_embed.add_field(name="Type", value=type_str, inline=True)
            
            dm_embed.add_field(
                name="Next Step",
                value="Go to a PC and click **View Trade Request** to respond!",
                inline=False
            )
            
            # Add Pokemon sprite as file attachment
            sprite_file = None
            try:
                sprite_path = f"/sprites/pokemon/{self.selected_pokemon.pokemonName}.png"
                full_sprite_path = get_sprite_path(sprite_path)
                
                if os.path.exists(full_sprite_path):
                    filename = f"{self.selected_pokemon.pokemonName}.png"
                    sprite_file = discord.File(full_sprite_path, filename=filename)
                    dm_embed.set_thumbnail(url=f"attachment://{filename}")
            except Exception as e:
                # Sprite loading failed, continue without sprite
                pass
            
            # Send DM with or without sprite
            if sprite_file:
                dm_message = await self.selected_member.send(embed=dm_embed, file=sprite_file)
            else:
                dm_message = await self.selected_member.send(embed=dm_embed)
            
            # Store message ID for potential editing later
            self.mixin.trade_service.update_notification_message_id(trade_id, str(dm_message.id))
            
        except discord.Forbidden:
            await interaction.followup.send(
                f"Trade request sent, but {self.selected_member.display_name} has DMs disabled. They'll see it when they visit a PC."
            )
        except Exception as e:
            await interaction.followup.send(f"Error sending DM: {str(e)}\nTrade still created - they'll see it at a PC.")
        
        # Confirm to sender
        await interaction.followup.send(
            f"✅ Trade request sent to **{self.selected_member.display_name}**!\nThey'll be notified to check their PC."
        )
        
        # Disable all controls
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    async def cancel(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.send_message("Trade cancelled.")
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)


class TradeReceiverResponseView(View):
    """View for receiver to accept/decline or select Pokemon"""
    
    def __init__(self, user: discord.User, trade_id: int, mixin: TradeMixin):
        super().__init__(timeout=300)
        self.user = user
        self.trade_id = trade_id
        self.mixin = mixin
        self.showing_selection = False
        self.pokemon = []
        self.selected_pokemon = None  # ADD THIS LINE
        
        # Accept button
        accept_button = Button(label="Accept & Choose Pokemon", style=ButtonStyle.green, custom_id="accept")
        accept_button.callback = self.accept_trade
        self.add_item(accept_button)
        
        # Decline button
        decline_button = Button(label="Decline", style=ButtonStyle.red, custom_id="decline")
        decline_button.callback = self.decline_trade
        self.add_item(decline_button)
    
    async def confirm_pokemon(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        if not self.selected_pokemon:
            await interaction.followup.send("No Pokemon selected.", ephemeral=True)
            return
        
        # Update trade with receiver's Pokemon
        success = self.mixin.trade_service.update_receiver_pokemon(self.trade_id, self.selected_pokemon.trainerId)
        
        if not success:
            await interaction.followup.send("Failed to update trade request.", ephemeral=True)
            return
        
        # Get trade details for notification
        trade = self.mixin.trade_service.get_trade_by_id(self.trade_id)
        
        # Notify sender via DM
        try:
            sender = await self.mixin.bot.fetch_user(int(trade['sender_discord_id']))
            
            dm_embed = discord.Embed(
                title="✉️ Trade Response Received!",
                description=f"**{self.user.display_name}** has responded to your trade!",
                color=discord.Color.green()
            )
            dm_embed.add_field(
                name="Next Step",
                value="Go to a PC and click **View Trade Response** to accept or decline!",
                inline=False
            )
            
            await sender.send(embed=dm_embed)
            
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending response notification: {e}")
        
        # Confirm to receiver
        await interaction.followup.send(
            "✅ Your Pokemon has been selected! Waiting for the other trainer to accept.",
            ephemeral=True
        )
        
        # Disable all controls
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    async def accept_trade(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Check if receiver has a Link Cable
        from services.inventoryclass import inventory as InventoryClass
        inv = InventoryClass(str(self.user.id))
        if inv.linkcable < 1:
            await interaction.followup.send(
                "🔗 You need a **Link Cable** to trade! Visit a Poké Mart to buy one.",
                ephemeral=True
            )
            return
        
        # Show Pokemon selection for the receiver
        self.showing_selection = True
        
        # Get receiver's Pokemon
        trainer = TrainerClass(str(self.user.id))
        active_pokemon = trainer.getActivePokemon()
        all_pokemon = trainer.getPokemon(False, True)
        
        for p in all_pokemon:
            p.load(pokemonId=p.trainerId)
        
        self.pokemon = [p for p in all_pokemon if p.trainerId != active_pokemon.trainerId]
        
        if not self.pokemon:
            await interaction.followup.send(
                "You don't have any Pokemon available to trade (excluding your active Pokemon).",
                ephemeral=True
            )
            return
        
        # Rebuild view with Pokemon selection
        self.clear_items()
        
        pokemon_options = [
            SelectOption(
                label=f"{p.nickName or p.pokemonName} (Lv.{p.currentLevel})",
                value=str(p.trainerId),
                description=f"{p.pokemonName} - {p.type1}" + (f"/{p.type2}" if p.type2 else ""),
                default=(self.selected_pokemon and p.trainerId == self.selected_pokemon.trainerId)
            )
            for p in self.pokemon[:25]
        ]
        
        pokemon_select = Select(
            placeholder="Select a Pokemon to offer...",
            options=pokemon_options,
            custom_id="pokemon_select"
        )
        pokemon_select.callback = self.pokemon_selected
        self.add_item(pokemon_select)
        
        confirm_button = Button(label="Confirm Trade", style=ButtonStyle.green, custom_id="confirm", disabled=True)
        confirm_button.callback = self.confirm_pokemon
        self.add_item(confirm_button)
        
        cancel_button = Button(label="Cancel", style=ButtonStyle.red, custom_id="cancel")
        cancel_button.callback = self.decline_trade
        self.add_item(cancel_button)
        
        await interaction.message.edit(
            content="Select a Pokemon to offer in return:",
            view=self
        )

    async def pokemon_selected(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        selected_pokemon_id = int(interaction.data['values'][0])
        
        # Find and store the selected Pokemon
        self.selected_pokemon = None
        for p in self.pokemon:
            if p.trainerId == selected_pokemon_id:
                self.selected_pokemon = p
                break
        
        if not self.selected_pokemon:
            await interaction.followup.send("Pokemon not found.", ephemeral=True)
            return
        
        # Rebuild the view with the selected Pokemon and add Confirm button
        self.clear_items()
        
        # Recreate the dropdown with the selected Pokemon marked as default
        pokemon_options = [
            SelectOption(
                label=f"{p.nickName or p.pokemonName} (Lv.{p.currentLevel})",
                value=str(p.trainerId),
                description=f"{p.pokemonName} - {p.type1}" + (f"/{p.type2}" if p.type2 else ""),
                default=(p.trainerId == selected_pokemon_id)
            )
            for p in self.pokemon[:25]
        ]
        
        pokemon_select = Select(
            placeholder="Select your Pokemon to trade...",
            options=pokemon_options,
            custom_id="pokemon_select"
        )
        pokemon_select.callback = self.pokemon_selected
        self.add_item(pokemon_select)
        
        # Add Confirm Trade button
        confirm_button = Button(label="Confirm Trade", style=ButtonStyle.green, custom_id="confirm")
        confirm_button.callback = self.confirm_pokemon
        self.add_item(confirm_button)
        
        # Add Cancel button
        cancel_button = Button(label="Cancel", style=ButtonStyle.red, custom_id="cancel")
        cancel_button.callback = self.decline_trade
        self.add_item(cancel_button)
        
        # Update the message
        pokemon_name = self.selected_pokemon.nickName or self.selected_pokemon.pokemonName
        await interaction.message.edit(
            content=f"Selected: **{pokemon_name}** (Level {self.selected_pokemon.currentLevel})\n\nClick **Confirm Trade** to proceed.",
            view=self
        )

    async def decline_trade(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Cancel trade
        await self.mixin.cancel_trade_notify(self.trade_id, str(self.user.id))
        
        await interaction.followup.send("Trade request declined.", ephemeral=True)
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

class TradeSenderAcceptView(View):
    """View for sender to accept/decline receiver's counter-offer"""
    
    def __init__(self, user: discord.User, trade_id: int, mixin: TradeMixin):
        super().__init__(timeout=300)
        self.user = user
        self.trade_id = trade_id
        self.mixin = mixin
        
        # Accept button
        accept_button = Button(label="Accept Trade", style=ButtonStyle.green, custom_id="accept")
        accept_button.callback = self.accept_trade
        self.add_item(accept_button)
        
        # Decline button
        decline_button = Button(label="Decline", style=ButtonStyle.red, custom_id="decline")
        decline_button.callback = self.decline_trade
        self.add_item(decline_button)
    
    async def accept_trade(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Execute the trade
        success, message = await self.mixin.execute_trade(self.trade_id)
        
        if success:
            await interaction.followup.send(
                "✅ Trade completed! Check your DMs for details.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Trade failed: {message}",
                ephemeral=True
            )
        
    
    async def decline_trade(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Cancel trade
        await self.mixin.cancel_trade_notify(self.trade_id, str(self.user.id))
        
        await interaction.followup.send("Trade request declined.", ephemeral=True)
        