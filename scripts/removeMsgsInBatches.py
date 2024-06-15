import csv
import asyncio
from time import sleep
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime
import discord
from init import database_connector, discord_connector
from config import channel_name, guild_id, role_id, remove_role_id_1

LOGGING_ENABLED = True
if LOGGING_ENABLED:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.disable(logging.CRITICAL)

def sanitize_channel_name(channel_name):
    """Sanitize the channel name to include only letters and numbers."""
    return ''.join(c for c in channel_name if c.isalnum())

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2)) 
async def delete_messages(discord_user_ids, sanitized_channel_name):
    logging.info(f"Removing: {discord_user_ids}")
    db = database_connector.connect()
    cursor = db.cursor()

    if discord_user_ids:
        placeholders = ', '.join(['%s'] * len(discord_user_ids))

        delete_query_channel = f"""
        DELETE FROM `{sanitized_channel_name}`
        WHERE user_id IN ({placeholders})
        """
        cursor.execute(delete_query_channel, discord_user_ids)
        logging.info(f"Deleted messages from {sanitized_channel_name}.")

        delete_query_discord = f"""
        DELETE FROM `discord`
        WHERE user_id IN ({placeholders})
        """
        cursor.execute(delete_query_discord, discord_user_ids)
        logging.info("Deleted messages from discord table.")

        for user_id in discord_user_ids:
            await manage_roles(user_id)
            sleep(0.1)

        db.commit()
    else:
        logging.info("No user IDs provided for deletion.")
    
    cursor.close()
    db.close()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2)) 
async def manage_roles(user_id):
    guild = discord_connector.get_guild(guild_id)
    if not guild:
        logging.error("Guild not found")
        return 0

    try:
        member = await guild.fetch_member(user_id)
    except discord.NotFound:
        logging.info(f"Member {user_id} not found in guild")
        return 0 
    except Exception as e:
        logging.error(f"Failed to fetch member {user_id}: {e}")
        return 0 
    
    updates = 0
    role_to_add = guild.get_role(remove_role_id_1)
    role_to_remove = guild.get_role(role_id) 

    if role_to_add and role_to_add not in member.roles:
        await member.add_roles(role_to_add)
        logging.info(f"User {member.name} ({user_id}) update: Added {role_to_add.name}")
        updates += 1

    if role_to_remove and role_to_remove in member.roles:
        await member.remove_roles(role_to_remove)
        logging.info(f"User {member.name} ({user_id}) update: Removed {role_to_remove.name}")
        updates += 1

    return updates


async def process_batches(discord_user_ids, sanitized_channel_name, batch_size=50):
    for i in range(0, len(discord_user_ids), batch_size):
        batch = discord_user_ids[i:i+batch_size]
        await delete_messages(batch, sanitized_channel_name)
        logging.info(f"Processed batch {i//batch_size + 1}/{(len(discord_user_ids) + batch_size - 1)//batch_size}")
        await asyncio.sleep(1)

@discord_connector.event
async def on_ready():
    logging.info(f'{discord_connector.user.name} has connected to Discord!')
    discord_user_ids = []
    with open('walletsToRemove.csv', 'r') as file:
        csvreader = csv.DictReader(file)
        for row in csvreader:
            discord_user_ids.append(row['discordUserId'])

    sanitized_channel_name = sanitize_channel_name(channel_name)
    await process_batches(discord_user_ids, sanitized_channel_name)

discord_connector.run_bot()
