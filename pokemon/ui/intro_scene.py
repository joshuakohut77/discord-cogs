from __future__ import annotations
from typing import List, Dict, Optional, Callable, TYPE_CHECKING
import discord
import os
from discord import ButtonStyle, Interaction
from discord.ui import Button, View, Modal, TextInput

if TYPE_CHECKING:
    from redbot.core.bot import Red

def get_sprite_path(relative_path: str) -> str:
    """Convert relative sprite path to absolute path"""
    # Remove leading slash if present
    if relative_path.startswith('/'):
        relative_path = relative_path[1:]
    
    # Get the directory of this file and go up to find the sprites folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming sprites folder is at the root of the pokemon module
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(root_dir, relative_path)


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
    def __init__(self, user_id: int, scenes: List[Dict], on_complete: Callable, sprite_path: str = None):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.scenes = scenes
        self.current_index = 0
        self.on_complete = on_complete
        self.sprite_path = sprite_path
        self.trainer_name = None
        self.message = None
        self.sprite_file = None
        self.sprite_filename = None
        
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
        
        # Add sprite if available and file was loaded
        if self.sprite_filename:
            embed.set_thumbnail(url=f"attachment://{self.sprite_filename}")
        
        # Add footer with progress
        embed.set_footer(text=f"Scene {self.current_index + 1}/{len(self.scenes)}")
        
        return embed
    
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
        
        # Update button label if this is the last scene
        if self.current_index == len(self.scenes) - 1:
            self.next_button.label = "Finish"
        
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
        
        # Update button label if this is the last scene
        if self.current_index == len(self.scenes) - 1:
            self.next_button.label = "Finish"
        
        await interaction.response.edit_message(embed=embed, view=self)


async def start_intro_scene(ctx, user_id: int, scenes: List[Dict], on_complete: Callable, sprite_path: str = None) -> discord.Message:
    """
    Start an intro scene sequence
    
    Args:
        ctx: Command context
        user_id: Discord user ID
        scenes: List of scene dictionaries
        on_complete: Async callback function when scene completes
        sprite_path: Optional path to character sprite image
    
    Scene dictionary format:
    {
        'title': 'Scene Title',
        'text': 'Scene text content. Use {name} for trainer name placeholder.',
        'color': discord.Color.blue(),  # Optional, defaults to blue
        'prompt_name': False  # Set to True to show name input modal after this scene
    }
    """
    view = IntroSceneView(user_id, scenes, on_complete, sprite_path)
    embed = view.create_embed()
    
    # If sprite path provided, try to load the file
    sprite_file = None
    sprite_loaded = False
    if sprite_path:
        try:
            # Try to load from local file system first
            full_sprite_path = get_sprite_path(sprite_path)
            
            # Check if file exists
            if os.path.exists(full_sprite_path):
                # Extract filename for attachment
                filename = os.path.basename(sprite_path)
                sprite_file = discord.File(full_sprite_path, filename=filename)
                view.sprite_filename = filename
                embed.set_thumbnail(url=f"attachment://{filename}")
                sprite_loaded = True
            else:
                raise FileNotFoundError("Sprite file not found locally")
        except Exception as e:
            print(f"Error loading trainer sprite from file: {e}")
            # Fallback to URL
            try:
                sprite_url = f"https://pokesprites.joshkohut.com{sprite_path}"
                embed.set_thumbnail(url=sprite_url)
            except Exception as url_error:
                print(f"Error loading trainer sprite from URL: {url_error}")
    
    message = await ctx.send(embed=embed, view=view, file=sprite_file)
    view.message = message
    return message