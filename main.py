import discord
from discord import Intents
import time
from discord.ext import commands
import random
import tempfile
from PIL import Image, ImageOps
import requests
from io import BytesIO
from typing import List
import aiohttp
import functools
import hashlib
from datetime import datetime, timedelta
import json
import asyncio
import logging
import os
from discord.ui import View, Button
from discord import ButtonStyle, PartialEmoji, ui
import cv2
from pathlib import Path
import numpy as np
from concurrent.futures import ThreadPoolExecutor





# Load user data from JSON file
users_file_path = './users.json'
if not os.path.exists(users_file_path):
    with open(users_file_path, 'w') as file:
        json.dump({}, file)

def load_users():
    with open(users_file_path, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(users_file_path, 'w') as file:
        json.dump(users, file, indent=2)



# Files for storing card and inventory data
card_file = 'cards.json'
inventory_file = 'inventories.json'

# Initialize the cards and user inventories
user_inventories = {}
cards = {}
user_binders = {}
cache = {}

blacklist = []

BLACKLIST_FILE = 'blacklist.json'
BINDER_DATA_FILE = "binders.json"

# Load and save user inventories from/to JSON
def load_inventory():
    try:
        with open(inventory_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_inventory():
    with open(inventory_file, 'w') as f:
        json.dump(user_inventories, f, indent=4)

# Load and save card data from JSON
def load_cards():
    try:
        with open(card_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cards(card_data):
    with open(card_file, 'w') as f:
        json.dump(card_data, f, indent=4)


# Load binders from a JSON file
def load_binders():
    global user_binders
    if os.path.exists(BINDER_DATA_FILE):
        with open(BINDER_DATA_FILE, 'r') as f:
            user_binders = json.load(f)
    else:
        user_binders = {}

# Save binders to a JSON file
def save_binders():
    with open(BINDER_DATA_FILE, 'w') as f:
        json.dump(user_binders, f, indent=4)




# Load blacklist from a file
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save blacklist to a file
def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f)

def check_blacklist(user_id):
    # Ensure user_id is a string for consistent comparison
    user_id_str = str(user_id)
    # Convert blacklist entries to strings for consistent comparison
    blacklist_str = [str(id) for id in blacklist]
    logging.debug(f"Current Blacklist: {blacklist_str}")
    logging.debug(f"Checking if User ID {user_id_str} is blacklisted.")
    return user_id_str not in blacklist_str

# Load cooldown data from JSON file
def load_cooldowns():
    try:
        with open("cooldowns.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cooldowns():
    with open("cooldowns.json", "w") as f:
        json.dump(cooldowns, f)

cooldowns = load_cooldowns()

# Check if a user is on cooldown
def is_on_cooldown(user_id, command):
    current_time = time.time()
    user_cooldowns = cooldowns.get(str(user_id), {})
    cooldown_time = user_cooldowns.get(command, 0)
    return current_time < cooldown_time

# Set a cooldown for a user
def set_cooldown(user_id, command, duration):
    current_time = time.time()
    if str(user_id) not in cooldowns:
        cooldowns[str(user_id)] = {}
    cooldowns[str(user_id)][command] = current_time + duration
    save_cooldowns()

# Load initial cards and inventories
cards = load_cards()
user_inventories = load_inventory()
# Load binders when the bot starts
load_binders()


intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/', intents=intents)

# Function to save image from Discord attachment and return the image path
async def save_image_from_attachment(attachment: discord.Attachment):
    # Ensure the images directory exists
    image_directory = './images/'
    if not os.path.exists(image_directory):
        os.makedirs(image_directory)

    # Save the image to a file
    image_bytes = await attachment.read()
    image_path = os.path.join(image_directory, attachment.filename)

    with open(image_path, 'wb') as f:
        f.write(image_bytes)

    return image_path

# Middleware: Check if user has started
async def check_user_started(interaction: discord.Interaction):
    users = load_users()
    user_id = str(interaction.user.id)
    if user_id not in users:
        await interaction.response.send_message(
            "You need to use `/start` before accessing any commands!", ephemeral=False
        )
        return False
    return True

@bot.tree.command(name="start", description="Initialize your bot usage.")
async def start(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    users = load_users()

    if user_id in users:
        await interaction.response.send_message("You have already started!", ephemeral=True)
        return

    # Step 1: Defer the response
    await interaction.response.defer(ephemeral=False)

    # Step 2: Simulate the process with message updates
    await interaction.followup.send("Starting initialization. Please wait . . .")
    await asyncio.sleep(1)
    await interaction.edit_original_response(content="Checking user . .")
    await asyncio.sleep(1.5)
    await interaction.edit_original_response(content="Preparing start . . .")
    await asyncio.sleep(2)
    await interaction.edit_original_response(content=". . . .")
    await asyncio.sleep(3)
    await interaction.edit_original_response(content="Please wait a moment, this might take 3 seconds . . .")
    await asyncio.sleep(2)
    await interaction.edit_original_response(content="Saving user . . .")

    # Step 3: Save user data
    users[user_id] = {"started": True, "timestamp": datetime.now().isoformat()}
    save_users(users)

    # Step 4: Final welcome message with an embed
    embed = discord.Embed(
        title="Welcome!",
        description="You can start to use the bot now! Have fun!",
        color=discord.Color.pink()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1314590451449462897/1317991417066426479/6968d88584ca746e4ae3f98f9317eb11.jpg?ex=6760b2a8&is=675f6128&hm=1237580ce5d6b37363c0d47f87c2a8fa2164abb60f085396869c0d3cd0bad188&")  # Replace with your image URL
    embed.set_footer(text="Thank you for joining us!")

    await asyncio.sleep(1.5)
    await interaction.edit_original_response(content=None, embed=embed)



users = load_users()

@bot.tree.command(name="card-add", description="Add a new card")
async def card_add(interaction: discord.Interaction, name: str, group: str, rarity: str, card_id: str, era: str, card_type: str, droppable: bool, image: discord.Attachment):
    allowed_role_name = "dev"
    allowed_server_id = 1333124771700801556

    if not await check_user_started(interaction):
        return

    if not check_blacklist(interaction.user.id):
        await interaction.response.send_message("You are blacklisted and cannot use this command.")
        return

    if interaction.guild.id != allowed_server_id:
        await interaction.response.send_message("This command can only be used in the specified server.")
        return

    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        embed = discord.Embed(
            title="Permission Denied",
            description="You do not have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.defer()

    if card_type.lower() not in ['booster', 'limited', 'regular', 'events', 'special', 'patreon', 'customs']:
        await interaction.followup.send("Invalid card type. Must be one of: booster, limited, regular, events, special, patreon, customs.")
        return

    image_path = await save_image_from_attachment(image)

    new_card = {
        'Name': name,
        'Group': group,
        'Rarity': rarity,
        'ID': card_id,
        'Era': era,
        'Type': card_type.lower(),
        'color': '#FF0800',
        'image_url': image_path,
        'droppable': droppable  # Set droppable field
    }

    cards[card_id] = new_card
    save_cards(cards)

    embed = discord.Embed(
        title="Card Added Successfully!",
        description=f"**Name**: {name}\n**Group**: {group}\n**Rarity**: {rarity}\n**ID**: {card_id}\n**Era**: {era}\n**Type**: {card_type}\n**Droppable**: {'Yes' if droppable else 'No'}",
        color=discord.Color.pink()
    )
    embed.set_image(url=f"attachment://{os.path.basename(image_path)}")

    await interaction.followup.send(embed=embed, file=discord.File(image_path))


users = load_users()


@bot.tree.command(name="card-edit", description="Edit an existing card or its ID")
async def card_edit(
    interaction: discord.Interaction,
    card_id: str,
    name: str = None,
    group: str = None,
    rarity: str = None,
    era: str = None,
    card_type: str = None,
    droppable: bool = None,
    image: discord.Attachment = None
):
    allowed_role_name = "dev"
    allowed_server_id = 1333124771700801556

    if not await check_user_started(interaction):
        return

    if not check_blacklist(interaction.user.id):
        await interaction.response.send_message("You are blacklisted and cannot use this command.")
        return

    if interaction.guild.id != allowed_server_id:
        await interaction.response.send_message("This command can only be used in the specified server.")
        return
    
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        embed = discord.Embed(
            title="Permission Denied",
            description="You do not have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.defer()

    # Load cards from storage
    try:
        with open("cards.json", "r") as f:
            cards = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        await interaction.followup.send("Error loading card data.")
        return

    old_card_id, *new_card_id = map(str.strip, card_id.split(","))
    new_card_id = new_card_id[0] if new_card_id else None

    if old_card_id not in cards:
        await interaction.followup.send(f"Card with ID `{old_card_id}` not found.")
        return

    # Handle ID change
    if new_card_id:
        if new_card_id in cards:
            await interaction.followup.send(f"The new card ID `{new_card_id}` already exists.")
            return
        cards[new_card_id] = cards.pop(old_card_id)
        cards[new_card_id]["ID"] = new_card_id
        old_card_id = new_card_id  # Update reference

    card = cards[old_card_id]

    # Update fields only if provided
    updated_fields = []
    
    if name:
        card["Name"] = name
        updated_fields.append("Name")
    
    if group:
        card["Group"] = group
        updated_fields.append("Group")

    if rarity:
        card["Rarity"] = rarity
        updated_fields.append("Rarity")

    if era:
        card["Era"] = era
        updated_fields.append("Era")

    if card_type:
        valid_types = ["booster", "limited", "regular", "events", "special", "patreon", "customs"]
        if card_type.lower() not in valid_types:
            await interaction.followup.send(f"Invalid card type. Must be one of: {', '.join(valid_types)}.")
            return
        card["Type"] = card_type.lower()
        updated_fields.append("Type")

    if droppable is not None:
        card["droppable"] = droppable
        updated_fields.append("Droppable")

    if image:
        try:
            image_path = await save_image_from_attachment(image)
            card["image_url"] = image_path
            updated_fields.append("Image URL")
        except Exception as e:
            await interaction.followup.send(f"Failed to save image: {e}")
            return

    # Save updates to file
    try:
        with open("cards.json", "w") as f:
            json.dump(cards, f, indent=4)
            f.flush()
            f.close()
    except Exception as e:
        await interaction.followup.send(f"Error saving card data: {e}")
        return

    # Update user inventories
    changes_applied = False
    for user_id, user_inventory in user_inventories.items():
        if old_card_id in user_inventory:
            inventory_card = user_inventory[old_card_id]["card"]
            
            if new_card_id:
                user_inventory[new_card_id] = user_inventory.pop(old_card_id)
                user_inventory[new_card_id]["card"]["ID"] = new_card_id
                inventory_card = user_inventory[new_card_id]["card"]

            if name:
                inventory_card["Name"] = name
            if group:
                inventory_card["Group"] = group
            if rarity:
                inventory_card["Rarity"] = rarity
            if era:
                inventory_card["Era"] = era
            if card_type:
                inventory_card["Type"] = card_type.lower()
            
            changes_applied = True

    if changes_applied:
        try:
            with open("inventories.json", "w") as f:
                json.dump(user_inventories, f, indent=4)
                f.flush()
                f.close()
        except Exception as e:
            await interaction.followup.send(f"Error saving inventory data: {e}")
            return

    # Prepare embed
    embed = discord.Embed(
        title="Card Edited Successfully!",
        description=f"**ID**: `{old_card_id}`\n**Droppable**: {'Yes' if card.get('droppable', False) else 'No'}",
        color=discord.Color.green()
    )
    embed.add_field(name="Name", value=card.get("Name", "N/A"), inline=True)
    embed.add_field(name="Group", value=card.get("Group", "N/A"), inline=True)
    embed.add_field(name="Rarity", value=card.get("Rarity", "N/A"), inline=True)
    embed.add_field(name="Era", value=card.get("Era", "N/A"), inline=True)
    embed.add_field(name="Type", value=card.get("Type", "N/A"), inline=True)
    embed.add_field(name="Internal ID", value=card.get("ID", "N/A"), inline=True)

    if updated_fields:
        embed.add_field(name="Updated Fields", value=", ".join(updated_fields), inline=False)
    else:
        embed.add_field(name="Updated Fields", value="No changes applied.", inline=False)

    await interaction.followup.send(embed=embed)







users = load_users()



# Directory for cached images
CACHE_DIR = Path("image_cache")
CACHE_DIR.mkdir(exist_ok=True)

async def combine_images(image_urls):
    images = []
    
    # Fetch images from URLs with retries
    async with aiohttp.ClientSession() as session:
        for url in image_urls:
            for attempt in range(3):  # Retry up to 3 times
                try:
                    async with session.get(url, timeout=20) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to fetch image from {url}")
                        image_data = BytesIO(await response.read())
                        images.append(Image.open(image_data))
                        break
                except Exception as e:
                    if attempt == 2:  # Log the failure after 3 attempts
                        raise Exception(f"Failed to fetch image from {url} after 3 attempts: {e}")

    # Calculate combined width and resize if necessary
    total_width = sum(image.width for image in images)
    max_height = max(image.height for image in images)
    max_total_width = 2048  # Limit total width
    scale_ratio = min(1.0, max_total_width / total_width)

    resized_images = [
        img.resize(
            (int(img.width * scale_ratio), int(img.height * scale_ratio)),
            Image.ANTIALIAS
        ) for img in images
    ]

    total_width = sum(img.width for img in resized_images)
    max_height = max(img.height for img in resized_images)

    # Create the combined image
    combined_image = Image.new('RGB', (total_width, max_height), (255, 255, 255))
    x_offset = 0
    for img in resized_images:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width

    # Save the combined image to a buffer
    output_buffer = BytesIO()
    combined_image.save(output_buffer, 'JPEG', quality=70)  # Compress to reduce size
    output_buffer.seek(0)

    # Ensure the image is within Discord's limits
    if output_buffer.tell() > 8000000:  # ~8 MB
        combined_image = combined_image.resize(
            (int(combined_image.width * 0.8), int(combined_image.height * 0.8)),
            Image.ANTIALIAS
        )
        output_buffer = BytesIO()
        combined_image.save(output_buffer, 'JPEG', quality=60)
        output_buffer.seek(0)

        if output_buffer.tell() > 8000000:  # Check again
            raise Exception("Combined image exceeds Discord's 8 MB limit even after resizing.")
    
    return output_buffer


# Temporary storage to prevent duplicate card drops
recent_drops = []

@bot.tree.command(name="drop", description="Drop a set of 3 cards")
async def drop(interaction: discord.Interaction):
    try:

        # Ensure the user has started
        if not await check_user_started(interaction):
            return


        # Check if the user is on cooldown for the `/drop` command
        if is_on_cooldown(interaction.user.id, "drop"):
            remaining_seconds = int(cooldowns[str(interaction.user.id)]["drop"] - time.time())
            remaining_minutes = remaining_seconds // 60
            remaining_seconds %= 60

            embed = discord.Embed(
                title="Cooldown Active!",
                description=(f"You are on cooldown for the `/drop` command. "
                             f"Please wait **{remaining_minutes} minutes and {remaining_seconds} seconds** before trying again."),
                color=discord.Color.red()
            )
            embed.set_footer(text="𝜗𝜚")
            await interaction.response.send_message(embed=embed)
            return

        # Set cooldown for the user
        set_cooldown(interaction.user.id, "drop", 300)  # 5-minute cooldown

        # Defer the interaction to extend processing time
        await interaction.response.defer()

        # Load card data
        with open("cards.json") as f:
            cards = json.load(f)

        # Organize cards by rarity
        rarity_levels = {
            rarity: [
                card for card in cards.values()
                if card['Rarity'] == rarity and card.get('droppable', True) and card['ID'] not in recent_drops
            ]
            for rarity in [
                "<:RS_Rarity:1333810442354561065>",
                "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
                "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
                "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
                "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
                "<:RS_MoonAndStar:1337840060367896617>",
                "<:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617>",
                "<:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617>",
                "<:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617>",
                "<:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617>",
                "<:WY_PixelStarPink:1337840265280491642>",
                "<:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642>",
                "<:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642>",
                "<:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642>",
                "<:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642>",
                "<:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898>",
                "<:valentines22:1340380136431816774><:valentines22:1340380136431816774><:valentines22:1340380136431816774><:valentines22:1340380136431816774><:valentines22:1340380136431816774>",
                "<:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481>",
            ]
        }

        # Define rarity weights
        rarity_weights = {
            "<:RS_Rarity:1333810442354561065>": 50,
            "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>": 30,
            "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>": 15,
            "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>": 4,
            "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>": 3,
            "<:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617><:RS_MoonAndStar:1337840060367896617>": 1,
            "<:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642><:WY_PixelStarPink:1337840265280491642>": 1,
            "<:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898><:RS_Shbd:1340021778646437898>": 1,
            "<:valentines22:1340380136431816774><:valentines22:1340380136431816774><:valentines22:1340380136431816774><:valentines22:1340380136431816774><:valentines22:1340380136431816774>": 1,
            "<:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481><:RS_IdolHBD:1342561783289876481>":1, 
        }

        # Select 3 unique cards with varying rarities
        drop_cards = []
        chosen_rarities = set()

        for _ in range(3):
            available_rarities = [
                r for r in rarity_levels.keys() if r not in chosen_rarities and rarity_levels[r]
            ]

            if not available_rarities:
                break  # Stop if no more unique rarities are available

            selected_rarity = random.choices(
                available_rarities,
                weights=[rarity_weights[r] for r in available_rarities],
                k=1
            )[0]

            card = random.choice(rarity_levels[selected_rarity])
            drop_cards.append(card)
            chosen_rarities.add(selected_rarity)

        if len(drop_cards) < 3:
            await interaction.followup.send("Not enough cards available to generate a proper drop. Please try again later.")
            return

        # Add dropped cards to recent_drops
        recent_drops.extend(card['ID'] for card in drop_cards)
        if len(recent_drops) > 100:
            recent_drops[:] = recent_drops[-100:]

        # Fetch image URLs for the cards
        image_urls = [card['image_url'] for card in drop_cards]

        # Combine card images
        try:
            combined_image = await combine_images(image_urls)
        except Exception as e:
            logging.error(f"Error combining images: {e}")
            await interaction.followup.send("Error combining card images. Please try again later.")
            return

        # Create and send embed
        embed = discord.Embed(
            title=f"{interaction.user.display_name} is dropping a set of 3 cards!",
            color=discord.Color.pink()
        )
        file = discord.File(fp=combined_image, filename="combined_cards.png")
        embed.set_image(url="attachment://combined_cards.png")

        # Use DropView for card interactions
        view = DropView(drop_cards, interaction.user)
        view.message = await interaction.followup.send(embed=embed, file=file, view=view)

        # Send another message with card names and rarities
        card_details = "\n".join(
            f"**{card['Name']}** - {card['Rarity']}" for card in drop_cards
        )
        await interaction.followup.send(f"(The reason why is this message appearing is because Sarang sometimes likes eating people's cards.. Here are the dropped cards:\n{card_details}", ephemeral=True)

    except Exception as e:
        logging.error(f"An error occurred in /drop: {e}")
        await interaction.followup.send("An unexpected error occurred. Please try again later.", ephemeral=True)





class DropView(discord.ui.View):
    def __init__(self, drop_cards, dropper):
        super().__init__(timeout=15)
        self.drop_cards = drop_cards
        self.claimed_cards = [None] * 3
        self.dropper = dropper
        self.message = None
        self.exclusive_time = time.time() + 5 # 10-second exclusivity window for the dropper

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="emoji_1", id=1333810377804353539),
        style=discord.ButtonStyle.gray,
        custom_id="claim_card_1"
    )
    async def claim_card_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_card(interaction, 0)

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="emoji_2", id=1333810544360030229),
        style=discord.ButtonStyle.gray,
        custom_id="claim_card_2"
    )
    async def claim_card_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_card(interaction, 1)

    @discord.ui.button(
        emoji=discord.PartialEmoji(name="emoji_3", id=1333810511988391947),
        style=discord.ButtonStyle.gray,
        custom_id="claim_card_3"
    )
    async def claim_card_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_card(interaction, 2)

    async def claim_card(self, interaction, card_index):
        # Check if the exclusivity period is still active
        if time.time() < self.exclusive_time and interaction.user != self.dropper:
            await interaction.response.send_message(
                "Only the drop owner can claim cards during the first 5 seconds!", ephemeral=True
            )
            return

        # Check if the user is on cooldown for claiming
        if is_on_cooldown(interaction.user.id, "claim"):
            # Calculate remaining cooldown time
            remaining = int(cooldowns[str(interaction.user.id)]["claim"] - time.time())
            minutes, seconds = divmod(remaining, 60)

            # Embed for cooldown message
            embed = discord.Embed(
                title="Claim Cooldown Active",
                description=(
                    f"You are on cooldown for claiming a card. "
                    f"Please wait **{minutes} minutes and {seconds} seconds** before trying again."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="౨ৎ")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if the user already claimed a card
        if interaction.user in self.claimed_cards:
            await interaction.response.send_message(
                "You can only claim one card from this drop.", ephemeral=True
            )
            return

        # Check if the card has already been claimed
        if self.claimed_cards[card_index]:
            await interaction.response.send_message(
                "This card is already claimed by someone!", ephemeral=True
            )
            return

        # Add the card to the user's inventory
        user_inventory = user_inventories.setdefault(str(interaction.user.id), {})
        card = self.drop_cards[card_index]
        ID = card["ID"]

        if ID in user_inventory:
            user_inventory[ID]["copies"] += 1
        else:
            user_inventory[ID] = {"card": card, "copies": 1}

        save_inventory()

        # Update claim status and send confirmation
        self.claimed_cards[card_index] = interaction.user
        claim_message = f"You claimed {card['Name']}!"
        await interaction.response.send_message(claim_message, ephemeral=True)

        # Set cooldown for claiming
        set_cooldown(interaction.user.id, "claim", 120)  # 2-minute cooldown

        # Disable the claimed button
        self.children[card_index].disabled = True
        if all(self.claimed_cards):
            self.stop()
            for child in self.children:
                child.disabled = True

        await self.message.edit(view=self)

    async def on_timeout(self):
        # Disable all buttons on timeout
        for child in self.children:
            child.disabled = True

        # Add an expired message button
        expired_button = discord.ui.Button(
            label="This drop has expired!", style=discord.ButtonStyle.gray, disabled=True
        )
        self.add_item(expired_button)

        if self.message:
            await self.message.edit(view=self)

        # Send a final status embed
        final_status_embed = self.build_final_status_embed()
        await self.message.channel.send(embed=final_status_embed)

    def build_final_status_embed(self):
        # Build an embed showing the drop results
        embed = discord.Embed(title="Drop Results", color=discord.Color.pink())

        for index, card in enumerate(self.drop_cards):
            if self.claimed_cards[index]:
                claimed_by = f"**Claimed by**: {self.claimed_cards[index].mention}"
            else:
                claimed_by = "**Status**: Not claimed"

            embed.add_field(
                name=f"**{card['Name']}**",
                value=(
                    f"**Group**: {card['Group']}\n"
                    f"**Rarity**: {card['Rarity']}\n"
                    f"**ID**: {card['ID']}\n"
                    f"{claimed_by}"
                ),
                inline=True
            )

        return embed




users = load_users()












PAGE_SIZE = 5  # Number of cards to show per page

class InventoryView(View):
    def __init__(self, user_inventory, embed, interaction, inventory_owner, viewing_user):
        super().__init__(timeout=None)  # Disable timeout to keep buttons visible
        self.user_inventory = user_inventory
        self.embed = embed
        self.interaction = interaction
        self.inventory_owner = inventory_owner  # The owner of the inventory
        self.viewing_user = viewing_user  # The user who is viewing the inventory
        self.current_page = 0
        self.total_pages = (len(self.user_inventory) - 1) // PAGE_SIZE + 1
        
        # Calculate the total card count (all copies included)
        self.total_card_count = sum(data.get('copies', 1) for data in user_inventory.values())

        # Update the embed for the initial page
        self.update_embed()

    def update_embed(self):
        # Convert the dictionary to a list of values (the card data)
        inventory_list = list(self.user_inventory.values())

        # Get the current page of cards
        start = self.current_page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_cards = inventory_list[start:end]

        # Clear the previous inventory display and add cards for the current page
        self.embed.clear_fields()
        for i, card_data in enumerate(page_cards, start=start + 1):
            card = card_data['card']  # Access the actual card data
            copies = card_data.get('copies', 1)  # Get the number of copies

            # Format card information as per the desired look
            card_info = (
                f"**{i}.** {card.get('Name', 'Unknown')}\n"
                f"**Group**: {card.get('Group', 'Unknown')}\n"
                f"**ID**: {card.get('ID', 'Unknown')}\n"
                f"**Era**: {card.get('Era', 'Unknown')}\n"
                f"**Rarity**: {card.get('Rarity', 'Unknown')}\n"
                f"**Copies**: {copies}\n"
            )

            self.embed.add_field(name="\u200B", value=card_info, inline=False)

        # Update footer with page and card count information
        self.embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages} | Cards: {self.total_card_count}")

    async def handle_button(self, interaction, page_change):
        # Ensure only the viewing user can interact with the buttons
        if interaction.user != self.viewing_user:
            await interaction.response.send_message("You can't interact with someone else's inventory.", ephemeral=True)
            return

        # Update the current page if the change is valid
        new_page = self.current_page + page_change
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.update_embed()
            await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label='', emoji=PartialEmoji(name="emoji_rewind", id=1333810473841197187), style=ButtonStyle.gray)
    async def rewind_page(self, interaction: discord.Interaction, button: Button):
        await self.handle_button(interaction, -self.current_page)

    @discord.ui.button(label='', emoji=PartialEmoji(name="emoji_back", id=1333810264533110823), style=ButtonStyle.gray)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        await self.handle_button(interaction, -1)

    @discord.ui.button(label='', emoji=PartialEmoji(name="emoji_forward", id=1333810342618468372), style=ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        await self.handle_button(interaction, 1)

    @discord.ui.button(label='', emoji=PartialEmoji(name="emoji_fastforward", id=1333810301212164248), style=ButtonStyle.gray)
    async def fastforward_page(self, interaction: discord.Interaction, button: Button):
        await self.handle_button(interaction, self.total_pages - self.current_page - 1)



users = load_users()

# Claim card logic
def claim_card(user_id, card_id, card_data):
    # Retrieve the user's inventory
    user_inventory = user_inventories.get(user_id, {})

    # Check if the card already exists in the inventory
    if card_id in user_inventory:
        # If it exists, increment the 'copies' count
        user_inventory[card_id]['copies'] += 1
    else:
        # If it doesn't exist, add it to the inventory with 'copies' = 1
        user_inventory[card_id] = {
            "card": card_data,
            "copies": 1
        }

    # Save the updated inventory
    user_inventories[user_id] = user_inventory

users = load_users()

# Map rarity numbers to emojis
RARITY_MAP = {
    1: "<:RS_Rarity:1333810442354561065>",
    2: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
    3: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
    4: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
    5: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
}




@bot.tree.command(name='inventory', description='Check your card inventory.')
async def inventory(
    interaction: discord.Interaction,
    name: str = None, 
    group: str = None, 
    era: str = None, 
    rarity: int = None,  # Add rarity as an optional search parameter
    user: discord.User = None
):
    # Determine the inventory owner
    sender_id = str(interaction.user.id)
    inventory_owner = user if user else interaction.user
    user_id = str(inventory_owner.id)

    if not await check_user_started(interaction):
        return
    

            # Check if sender is blacklisted
    if not check_blacklist(sender_id):
        embed = discord.Embed(
            title="Access Denied",
            description="You are blacklisted and cannot use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        return

    # Retrieve the specified user's inventory
    user_inventory = user_inventories.get(user_id, {})

    # Check if the inventory is empty
    if not user_inventory:
        await interaction.response.send_message(f"{inventory_owner.display_name}'s inventory is empty.", ephemeral=True)
        return

    # Convert rarity number to emoji string
    rarity_emoji = RARITY_MAP.get(rarity, None) if rarity else None

    # Filter the inventory based on search parameters
    filtered_inventory = {
        card_id: data for card_id, data in user_inventory.items()
        if (not name or name.lower() in data['card'].get('Name', '').lower()) and
           (not group or group.lower() in data['card'].get('Group', '').lower()) and
           (not era or era.lower() in data['card'].get('Era', '').lower()) and
           (not rarity_emoji or rarity_emoji == data['card'].get('Rarity', ''))
    }

    # Check if the filtered inventory is empty
    if not filtered_inventory:
        await interaction.response.send_message("No cards found matching your search criteria.", ephemeral=True)
        return

    # Create the embed for the filtered inventory
    embed = discord.Embed(
        title=f"{inventory_owner.display_name}'s Inventory",
        color=discord.Color.pink()
    )

    # Create the InventoryView and send the message with embed and view
    view = InventoryView(
        user_inventory=filtered_inventory,
        embed=embed,
        interaction=interaction,
        inventory_owner=inventory_owner,
        viewing_user=interaction.user  # Ensure viewing_user is passed
    )
    await interaction.response.send_message(embed=embed, view=view)




users = load_users()



@bot.tree.command(name='blacklist', description='Blacklist a user from using the bot')
async def blacklist_command(interaction: discord.Interaction, user: discord.Member):
    allowed_role_name = "• Ryu Staff"  # The name of the role that can blacklist users
    allowed_server_id = 1307394208130404443  # Replace with your server ID

    if not await check_user_started(interaction):
        return

    # Check if the command is being used in the allowed server
    if interaction.guild.id != allowed_server_id:
        await interaction.response.send_message("This command can only be used in the specified server.")
        return

    # Check if the user has the allowed role
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.")
        return

    try:
        if user.id not in blacklist:
            blacklist.append(user.id)
            save_blacklist(blacklist)
            await interaction.response.send_message(f"{user.name} has been blacklisted.")
        else:
            await interaction.response.send_message(f"{user.name} is already blacklisted.")
    except Exception as e:
        logging.error(f"Error in blacklist_command: {e}")
        await interaction.response.send_message("An error occurred while executing the command.")

users = load_users()

@bot.tree.command(name='unblacklist', description='Remove a user from the blacklist')
async def unblacklist_command(interaction: discord.Interaction, user: discord.Member):
    allowed_role_name = "• Ryu Staff"  # The name of the role that can unblacklist users
    allowed_server_id = 1307394208130404443 # Replace with your server ID

    if not await check_user_started(interaction):
        return

    # Check if the command is being used in the allowed server
    if interaction.guild.id != allowed_server_id:
        await interaction.response.send_message("This command can only be used in the specified server.")
        return

    # Check if the user has the allowed role
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.")
        return

    try:
        if user.id in blacklist:
            blacklist.remove(user.id)
            save_blacklist(blacklist)
            await interaction.response.send_message(f"{user.name} has been removed from the blacklist.")
        else:
            await interaction.response.send_message(f"{user.name} is not in the blacklist.")
    except Exception as e:
        logging.error(f"Error in unblacklist_command: {e}")
        await interaction.response.send_message("An error occurred while executing the command.")

users = load_users()

# Constants
BINDER_PAGE_SIZE = 6
PLACEHOLDER_IMAGE_PATH = "path/to/placeholder.png"  # Add the path to your placeholder image

async def combine_images(image_paths_or_urls, layout="grid", max_cards=3, scale_factor=4):  
    logging.debug(f"Combining images with paths/URLs: {image_paths_or_urls}")
    images = []

    for path_or_url in image_paths_or_urls:
        if os.path.exists(path_or_url):
            try:
                image = Image.open(path_or_url).convert("RGBA")
                images.append(image)
                logging.debug(f"Loaded image from local path: {path_or_url}")
            except Exception as e:
                logging.error(f"Error opening image from local path {path_or_url}: {e}")
                raise
        else:
            try:
                response = requests.get(path_or_url)
                if "image" not in response.headers['Content-Type']:
                    raise ValueError(f"URL {path_or_url} did not return a valid image.")
                image = Image.open(BytesIO(response.content)).convert("RGBA")
                images.append(image)
                logging.debug(f"Fetched image from URL: {path_or_url}")
            except Exception as e:
                logging.error(f"Error fetching image from URL {path_or_url}: {e}")
                raise

    # Get the dimensions of each image
    widths, heights = zip(*(i.size for i in images))

    # Determine layout: grid for binder or row for drop
    if layout == "grid" and max_cards > 1:
        # Assuming a 2-row grid for binder (adjust as needed)
        rows = (len(images) + 2) // 3  # 2 or 3 rows depending on the number of cards
        max_card_height = int(max(heights) * (scale_factor / 2))  # Reduce scale for grid
    else:
        rows = 1
        max_card_height = int(max(heights) * scale_factor)

    max_card_widths = [int(w * (max_card_height / h)) for w, h in zip(widths, heights)]
    total_width = sum(max_card_widths) if rows == 1 else 3 * max(max_card_widths)
    total_height = rows * max_card_height

    logging.debug(f"New image dimensions: total_width={total_width}, total_height={total_height}")

    # Create a new image for the grid or row
    new_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

    # Paste images
    x_offset, y_offset = 0, 0
    for index, (im, new_width) in enumerate(zip(images, max_card_widths)):
        resized_image = im.resize((new_width, max_card_height), Image.Resampling.LANCZOS)
        new_image.paste(resized_image, (x_offset, y_offset), resized_image)

        if layout == "grid":
            # Update x and y offsets for grid layout
            if (index + 1) % 3 == 0:  # Move to next row
                x_offset = 0
                y_offset += max_card_height
            else:
                x_offset += new_width
        else:
            x_offset += new_width  # In a row layout, just move along x-axis

    # Save the image to an in-memory buffer
    output_buffer = BytesIO()
    new_image.save(output_buffer, 'PNG')
    output_buffer.seek(0)
    logging.debug("Combined image saved to buffer.")
    return output_buffer


@bot.tree.command(name="viewcard", description="View card details and ownership.")
async def view_card(interaction: discord.Interaction, card_id: str):
    sender_id = str(interaction.user.id)
    """Command to view card details and ownership."""

    
    if not await check_user_started(interaction):
        return
    

        # Check if sender is blacklisted
    if not check_blacklist(sender_id):
        embed = discord.Embed(
            title="Access Denied",
            description="You are blacklisted and cannot use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        return

    # Load card details from cards.json
    try:
        with open('cards.json', 'r') as f:
            cards = json.load(f)
    except FileNotFoundError:
        await interaction.response.send_message("Card database not found.", ephemeral=True)
        return

    # Fetch the specific card
    card = cards.get(card_id)
    if not card:
        await interaction.response.send_message(f"Card with ID `{card_id}` not found.", ephemeral=True)
        return

    # Load inventory details from inventories.json
    try:
        with open('inventories.json', 'r') as f:
            inventories = json.load(f)
    except FileNotFoundError:
        inventories = {}

    # Check user ownership
    user_id = str(interaction.user.id)
    user_inventory = inventories.get(user_id, {})
    owned_card_data = user_inventory.get(card_id)  # Fetch the nested dictionary for the card, if it exists
    owned_copies = owned_card_data["copies"] if isinstance(owned_card_data, dict) else 0  # Extract only the 'copies' value

    # Create the embed for the card details
    embed = discord.Embed(
        title=f"{card['Name']} ({card['ID']})",
        color=int("FFC0CB", 16),  # Convert HEX color to integer
        description=(
            f"**Name:** {card['Name']}\n"
            f"**Group:** {card['Group']}\n"
            f"**Rarity:** {card['Rarity']}\n"
            f"**Era:** {card['Era']}\n"
            f"**Type:** {card['Type']}\n"
            f"**Droppable:** {'Yes' if card['droppable'] else 'No'}\n"
            f"**Owned Copies:** {owned_copies}"
        )
    )

    # Handle local image
    image_path = Path(card["image_url"])
    if image_path.is_file():
        file = discord.File(fp=image_path, filename=image_path.name)
        embed.set_image(url=f"attachment://{image_path.name}")
        await interaction.response.send_message(embed=embed, file=file)
    else:
        embed.description += "\n\n*Image not found.*"
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="gift", description="Send a cute gift to another user!")
async def gift_card(interaction: discord.Interaction, receiver: discord.User, card_id: str, quantity: int = 1):
    sender_id = str(interaction.user.id)
    receiver_id = str(receiver.id)

    if not await check_user_started(interaction):
        return

    # Check if sender is blacklisted
    if not check_blacklist(sender_id):
        embed = discord.Embed(
            title="Access Denied",
            description="You are blacklisted and cannot use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        return

    sender_inventory = user_inventories.get(sender_id, {})

    # Check if sender has enough copies of the card
    if card_id not in sender_inventory or sender_inventory[card_id]["copies"] < quantity:
        embed = discord.Embed(
            title="🌸",
            description=f"You don't have enough {card_id} to send. Maybe try collecting a few more first! 🌸",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Store card details before deleting from sender's inventory
    card_details = sender_inventory[card_id]["card"]

    # Transfer cards
    sender_inventory[card_id]["copies"] -= quantity
    if sender_inventory[card_id]["copies"] == 0:
        del sender_inventory[card_id]  # Remove card from sender if 0 copies left

    receiver_inventory = user_inventories.get(receiver_id, {})
    if card_id in receiver_inventory:
        receiver_inventory[card_id]["copies"] += quantity
    else:
        receiver_inventory[card_id] = {
            "card": card_details,  # Use stored card details
            "copies": quantity
        }

    user_inventories[sender_id] = sender_inventory
    user_inventories[receiver_id] = receiver_inventory
    save_inventory()

    # Send confirmation embed
    embed = discord.Embed(
        description=(
            f"🪷 ◟**{receiver.mention}**, You've received a gift from **{interaction.user.mention}!**\n"
            f"• **ID:** `{card_id}`\n"
            f"• **Copies:** `{quantity}`"
        ),
        color=discord.Color.from_rgb(255, 192, 203)
    )
    await interaction.response.send_message(embed=embed)





@bot.tree.command(name="multigift", description="Send multiple gifts to a user!")
async def multigift(
    interaction: discord.Interaction,
    receiver: discord.User,
    card1: str, quantity1: int,
    card2: str = None, quantity2: int = 1,
    card3: str = None, quantity3: int = 1,
    card4: str = None, quantity4: int = 1,
    card5: str = None, quantity5: int = 1,
):
    sender_id = str(interaction.user.id)
    receiver_id = str(receiver.id)

    if not await check_user_started(interaction):
        return
    

        # Check if sender is blacklisted
    if not check_blacklist(sender_id):
        embed = discord.Embed(
            title="Access Denied",
            description="You are blacklisted and cannot use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        return
    
    sender_inventory = user_inventories.get(sender_id, {})
    receiver_inventory = user_inventories.get(receiver_id, {})

    if not sender_inventory:
        await interaction.response.send_message("You have no cards to gift! 💔", ephemeral=True)
        return


    # Collect all gift requests
    gifts = [
        (card1, quantity1),
        (card2, quantity2),
        (card3, quantity3),
        (card4, quantity4),
        (card5, quantity5)
    ]

    gifted_cards = []

    for card_id, quantity in gifts:
        if card_id is None:
            continue

        # Check if sender has enough copies
        if card_id not in sender_inventory or sender_inventory[card_id]["copies"] < quantity:
            await interaction.response.send_message(f"You don’t have enough of **{card_id}** to gift. 🌸", ephemeral=True)
            return

        # Store card details before removing
        card_details = sender_inventory[card_id]["card"]

        # Deduct from sender
        sender_inventory[card_id]["copies"] -= quantity
        if sender_inventory[card_id]["copies"] == 0:
            del sender_inventory[card_id]  # Remove card if count is 0

        # Add to receiver
        if card_id in receiver_inventory:
            receiver_inventory[card_id]["copies"] += quantity
        else:
            receiver_inventory[card_id] = {
                "card": card_details,  # Use stored card details
                "copies": quantity
            }

        gifted_cards.append((card_id, quantity))

    # Save updated inventories
    user_inventories[sender_id] = sender_inventory
    user_inventories[receiver_id] = receiver_inventory
    save_inventory()

    # Create embed with new format
    embed = discord.Embed(
        description=(
            f"🪷 ◟**{receiver.mention}**, You've received gifts from **{interaction.user.mention}!**\n\n"
            + "\n".join([f"• **ID:** `{card_id}`\n  • **Copies:** `{quantity}`" for card_id, quantity in gifted_cards])
        ),
        color=discord.Color.from_rgb(255, 182, 193),
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1333124771700801559/1336423910979403857/828992d4aa8c7fa5b99f032a")

    await interaction.response.send_message(embed=embed)



def load_cards_from_json(file_path="cards.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"cards": {}}
    except json.JSONDecodeError:
        return {"cards": {}}



@bot.tree.command(name="staff_gift", description="Staff gift cards to a user.")
async def staff_gift(
    interaction: discord.Interaction, 
    receiver: discord.User, 
    card_id: str, 
    quantity: int = 1
):
    sender_id = str(interaction.user.id)
    receiver_id = str(receiver.id)

    if not await check_user_started(interaction):
        return

    # Check if sender or receiver is blacklisted
    if not check_blacklist(sender_id) or not check_blacklist(receiver_id):
        embed = discord.Embed(
            title="Access Denied",
            description="One or both users are blacklisted and cannot use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    allowed_role_name = "• NAYA Staff"
    allowed_server_id = 1307394208130404443

    if interaction.guild.id != allowed_server_id:
        await interaction.response.send_message(
            "This command can only be used in the specified server.",
            ephemeral=True
        )
        return

    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True
        )
        return

    # Load card data from cards.json
    card_data = load_cards_from_json("cards.json")
    available_cards = card_data  # Since cards.json directly contains card IDs

    # Check if the card exists
    if card_id not in available_cards:
        embed = discord.Embed(
            title="Card Not Found",
            description=f"The card `{card_id}` does not exist in the system.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Store card details
    card_details = available_cards[card_id]

    # Add the card to the receiver's inventory
    receiver_inventory = user_inventories.get(receiver_id, {})
    if card_id in receiver_inventory:
        receiver_inventory[card_id]["copies"] += quantity
    else:
        receiver_inventory[card_id] = {
            "card": card_details,
            "copies": quantity
        }

    user_inventories[receiver_id] = receiver_inventory
    save_inventory()

    # Create embed
    embed = discord.Embed(
        description=(
            f"🪷 ◟ **{receiver.mention}**, You've received a gift from **{interaction.user.mention}!**\n"
            f"• **ID:** `{card_id}`\n"
            f"• **Copies:** `{quantity}`"
        ),
        color=discord.Color.from_rgb(255, 192, 203)
    )

    await interaction.response.send_message(embed=embed)







TARGET_CHANNEL_ID = 1333124771700801559  # channel ID
FIELDS_PER_EMBED = 25

        # Rarity Emojis
RARITY_EMOJIS = {
    1: "<:RS_Rarity:1333810442354561065>",
    2: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
    3: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
    4: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
    5: "<:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065><:RS_Rarity:1333810442354561065>",
} 

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    print("Bot is connected and ready.")
    await client.wait_until_ready()

    try:
        print("Reading cards.json...")
        with open("cards.json", "r") as f:
            cards_data = json.load(f)

        if not cards_data:
            print("No cards found.")
            return

        channel = client.get_channel(TARGET_CHANNEL_ID)
        if channel is None:
            print(f"Channel with ID {TARGET_CHANNEL_ID} not found.")
            return

        print(f"Found target channel: {channel.name} (ID: {channel.id})")

        card_items = list(cards_data.items())  # Convert dictionary to list for slicing
        total_cards = len(card_items)
        print(f"Loaded {total_cards} cards.")

        # Prepare and send embeds in batches
        for i in range(0, total_cards, FIELDS_PER_EMBED):
            embed = discord.Embed(
                title="Card List",
                description=f"Showing cards {i + 1} to {min(i + FIELDS_PER_EMBED, total_cards)}",
                color=0x1ABC9C,
            )

            for card_key, card_data in card_items[i:i + FIELDS_PER_EMBED]:
                rarity = card_data.get("Rarity", "Unknown Rarity")
                embed.add_field(
                    name=f"Card Key: {card_key}", 
                    value=f"Rarity: {rarity}", 
                    inline=False
                )

            print(f"Sending embed for cards {i + 1} to {min(i + FIELDS_PER_EMBED, total_cards)}")
            await channel.send(embed=embed)

        print("All embeds sent successfully!")

    except json.JSONDecodeError:
        print("Error reading or parsing cards.json.")
    except discord.errors.HTTPException as http_err:
        print(f"Discord HTTP Exception: {http_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)!")
    except Exception as e:
        print(f"Sync failed: {e}")


async def setup_hook(self):
    await self.tree.sync()


# Run the bot
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


bot.run('MTMxNDMxMzk2NDQ2OTA5MjM1Mw.GlBubC.YWMSLdESl3XmwTTvamIPc3kmRHtF1t0phKpDms')