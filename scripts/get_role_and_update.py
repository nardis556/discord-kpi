import asyncio
import logging
from datetime import datetime
from init import database_connector, discord_connector
from config import channel_name, guild_id, role_id, remove_role_id_1
import discord
from tenacity import retry, stop_after_attempt, wait_fixed

LOGGING_ENABLED = True
if LOGGING_ENABLED:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.disable(logging.CRITICAL)

def sanitize_channel_name(channel_name):
    """Sanitize the channel name to include only letters and numbers."""
    return ''.join(c for c in channel_name if c.isalnum())

async def process_channel_data():
    db = database_connector.connect()
    cursor = db.cursor()
    sanitized_channel_name = sanitize_channel_name(channel_name)
    start_date = datetime(2024, 4, 29)
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    offset = 0
    batch_size = 100
    total_updates = 0 
    print(f'Searching from {start_date_str}')

    while True:
        select_query = f"""
        SELECT user_id FROM `{sanitized_channel_name}`
        WHERE timestamp >= '{start_date_str}'
        LIMIT {batch_size} OFFSET {offset}
        """
        cursor.execute(select_query)
        user_ids = cursor.fetchall()

        if not user_ids:
            break

        for (user_id,) in user_ids:
            updates = await manage_roles(user_id)
            total_updates += updates
            await asyncio.sleep(0.05)

        # await asyncio.sleep(0.1)
        offset += batch_size
        db.commit()

    cursor.close()
    db.close()
    logging.info(f"Total role updates performed: {total_updates}")

async def manage_roles(user_id):
    guild = discord_connector.get_guild(guild_id)
    updates = 0
    if not guild:
        logging.error("Guild not found")
        return updates

    try:
        member = await guild.fetch_member(user_id)
    except discord.NotFound:
        logging.info(f"Member {user_id} not found in guild")
        return updates
    except Exception as e:
        logging.error(f"Failed to fetch member {user_id}: {e}")
        return updates

    role_to_add = guild.get_role(role_id)
    role_to_remove = guild.get_role(remove_role_id_1)

    async def retry_operation(operation, *args, max_retries=3, delay=1):
        for attempt in range(max_retries):
            try:
                await operation(*args)
                return True
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed for {operation.__name__}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (2 ** attempt))
        return False

    if role_to_add and role_to_add not in member.roles:
        if await retry_operation(member.add_roles, role_to_add):
            logging.info(f"User {member.name} ({user_id}) update: Added {role_to_add.name}")
            updates += 1

    if role_to_remove and role_to_remove in member.roles:
        if await retry_operation(member.remove_roles, role_to_remove):
            logging.info(f"User {member.name} ({user_id}) update: Removed {role_to_remove.name}")
            updates += 1

    return updates

@discord_connector.event
async def on_ready():
    logging.info(f'{discord_connector.user.name} has connected to Discord!')
    asyncio.create_task(process_channel_data())

discord_connector.run_bot()