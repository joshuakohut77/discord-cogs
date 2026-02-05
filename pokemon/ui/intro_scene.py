from __future__ import annotations
from typing import List, Dict, Optional, Callable, TYPE_CHECKING
import discord
import os
from discord import ButtonStyle, Interaction
from discord.ui import Button, View, Modal, TextInput

if TYPE_CHECKING:
    from redbot.core.bot import Red

# Import the helper function from the correct location
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.pathhelpers import get_sprite_path


class NameInputModal(Modal):
    """Modal for capturing trainer name"""
    def __init__(self, callback_func: Callable):
        super().__init__(title="Enter Your Name")
        self.callback_func = callback_func
        
        self.name_input = TextInput(
            label="What's your name?",
            placeholder="Enter your trainer name...",
            max_length=20,
            required=True
        )
        self.add_item(self.name_input)
    
    async def on_submit(self, interaction: Interaction):
        await self.callback_func(interaction, self.name_input.value)


class IntroSceneView(View):
    """View for navigating through intro scenes"""
    def __init__(self, user_id: int, scenes: List[Dict], on_complete: Callable):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.scenes = scenes
        self.current_index = 0
        self.on_complete = on_complete
        self.trainer_name = None
        self.message = None
        
        # Create next button
        self.next_button = Button(style=ButtonStyle.primary, label="Next", custom_id="next")
        self.next_button.callback = self.on_next_click
        self.add_item(self.next_button)
    
    def create_embed(self) -> discord.Embed:
        """Create embed for current scene"""
        scene = self.scenes[self.current_index]
        
        # Replace {name} placeholder if trainer name is set
        text = scene['text']
        if self.trainer_name:
            text = text.replace('{name}', self.trainer_name)
        
        embed = discord.Embed(
            title=scene.get('title', ''),
            description=text,
            color=scene.get('color', discord.Color.blue())
        )
        
        # Add footer with progress
        embed.set_footer(text=f"Scene {self.current_index + 1}/{len(self.scenes)}")
        
        return embed
    
    def get_current_sprite_file(self) -> Optional[discord.File]:
        """Get sprite file for current scene if available"""
        scene = self.scenes[self.current_index]
        sprite_path = scene.get('sprite_path')
        
        if not sprite_path:
            return None
        
        try:
            # Try to load from local file system first
            full_sprite_path = get_sprite_path(sprite_path)
            
            # Check if file exists
            if os.path.exists(full_sprite_path):
                # Extract filename for attachment
                filename = os.path.basename(sprite_path)
                return discord.File(full_sprite_path, filename=filename)
            else:
                raise FileNotFoundError("Sprite file not found locally")
        except Exception as e:
            print(f"Error loading sprite from file: {e}")
            return None
    
    def add_sprite_to_embed(self, embed: discord.Embed) -> None:
        """Add sprite to embed (either as attachment or URL)"""
        scene = self.scenes[self.current_index]
        sprite_path = scene.get('sprite_path')
        
        if not sprite_path:
            return
        
        # Check if we have a file attachment
        filename = os.path.basename(sprite_path)
        embed.set_image(url=f"attachment://{filename}")
    
    async def on_next_click(self, interaction: Interaction):
        """Handle next button click"""
        # Check if this is for the right user
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This intro scene is not for you!", ephemeral=True)
            return
        
        # Check if current scene requires name input
        current_scene = self.scenes[self.current_index]
        if current_scene.get('prompt_name', False) and self.trainer_name is None:
            # Show modal for name input
            modal = NameInputModal(self.on_name_submit)
            await interaction.response.send_modal(modal)
            return
        
        # Move to next scene
        self.current_index += 1
        
        # Check if we've reached the end
        if self.current_index >= len(self.scenes):
            await interaction.response.defer()
            await self.on_complete(interaction, self.trainer_name)
            return
        
        # Update embed with next scene
        embed = self.create_embed()
        sprite_file = self.get_current_sprite_file()
        
        # Add sprite to embed if available
        if sprite_file:
            self.add_sprite_to_embed(embed)
        
        # Update button label if this is the last scene
        if self.current_index == len(self.scenes) - 1:
            self.next_button.label = "Finish"
        
        # Edit message with new sprite file if available
        if sprite_file:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[sprite_file])
        else:
            # Fallback to URL if local file not available
            scene = self.scenes[self.current_index]
            sprite_path = scene.get('sprite_path')
            if sprite_path:
                try:
                    sprite_url = f"https://pokesprites.joshkohut.com{sprite_path}"
                    embed.set_image(url=sprite_url)
                except:
                    pass
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_name_submit(self, interaction: Interaction, name: str):
        """Handle name submission from modal"""
        self.trainer_name = name
        
        # Move to next scene after name input
        self.current_index += 1
        
        # Check if we've reached the end
        if self.current_index >= len(self.scenes):
            await interaction.response.defer()
            await self.on_complete(interaction, self.trainer_name)
            return
        
        # Update embed with next scene
        embed = self.create_embed()
        sprite_file = self.get_current_sprite_file()
        
        # Add sprite to embed if available
        if sprite_file:
            self.add_sprite_to_embed(embed)
        
        # Update button label if this is the last scene
        if self.current_index == len(self.scenes) - 1:
            self.next_button.label = "Finish"
        
        # Edit message with new sprite file if available
        if sprite_file:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[sprite_file])
        else:
            # Fallback to URL if local file not available
            scene = self.scenes[self.current_index]
            sprite_path = scene.get('sprite_path')
            if sprite_path:
                try:
                    sprite_url = f"https://pokesprites.joshkohut.com{sprite_path}"
                    embed.set_image(url=sprite_url)
                except:
                    pass
            await interaction.response.edit_message(embed=embed, view=self)


async def start_intro_scene(ctx, user_id: int, scenes: List[Dict], on_complete: Callable) -> discord.Message:
    """
    Start an intro scene sequence
    
    Args:
        ctx: Command context
        user_id: Discord user ID
        scenes: List of scene dictionaries
        on_complete: Async callback function when scene completes
    
    Scene dictionary format:
    {
        'title': 'Scene Title',
        'text': 'Scene text content. Use {name} for trainer name placeholder.',
        'color': discord.Color.blue(),  # Optional, defaults to blue
        'prompt_name': False,  # Set to True to show name input modal after this scene
        'sprite_path': 'sprites/trainers/oak.png'  # Optional, sprite for this specific scene
    }
    """
    view = IntroSceneView(user_id, scenes, on_complete)
    embed = view.create_embed()
    
    # Get sprite for first scene if available
    sprite_file = view.get_current_sprite_file()
    
    # Add sprite to embed if available
    if sprite_file:
        view.add_sprite_to_embed(embed)
        message = await ctx.send(embed=embed, view=view, file=sprite_file)
    else:
        # Fallback to URL if local file not available
        sprite_path = scenes[0].get('sprite_path')
        if sprite_path:
            try:
                sprite_url = f"https://pokesprites.joshkohut.com{sprite_path}"
                embed.set_image(url=sprite_url)
            except:
                pass
        message = await ctx.send(embed=embed, view=view)
    
    view.message = message
    return message