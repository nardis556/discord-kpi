import csv
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime
import sys
import discord
from init import database_connector, discord_connector
from config import channel_name, guild_id, role_id, remove_role_id_1, alert_user_channel


guild = None
channel = None


LOGGING_ENABLED = True
if LOGGING_ENABLED:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
else:
    logging.disable(logging.CRITICAL)


def sanitize_channel_name(channel_name):
    """Sanitize the channel name to include only letters and numbers."""
    return "".join(c for c in channel_name if c.isalnum())


async def alert_user(user_id):
    global channel
    try:
        await channel.send(
            f"<@{user_id}> The next competition is about to begin! Head over to #wl-start-here and add a NEW WALLET to participate"
        )
    except Exception as e:
        return e


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def delete_messages(discord_user_ids, sanitized_channel_name):
    db = database_connector.connect()
    cursor = db.cursor()
    
    guild = discord_connector.get_guild(guild_id)
    channel = discord_connector.get_channel(alert_user_channel)
    
    role_to_add = guild.get_role(remove_role_id_1)
    role_to_remove = guild.get_role(role_id)

    if discord_user_ids:
        placeholders = ", ".join(["%s"] * len(discord_user_ids))

        delete_query_channel = f"""
        DELETE FROM `{sanitized_channel_name}`
        WHERE user_id IN ({placeholders})
        """
        cursor.execute(delete_query_channel, discord_user_ids)
        logging.info(f"Deleted messages from {sanitized_channel_name}.")

        # delete_query_discord = f"""
        # DELETE FROM `discord`
        # WHERE user_id IN ({placeholders})
        # """

        delete_query_discord = f"""
        DELETE FROM `discord`
        WHERE user_id IN ({placeholders}) AND content LIKE '%0x%'
        """

        cursor.execute(delete_query_discord, discord_user_ids)

        db.commit()

        logging.info("Deleted messages from discord table.")

        updated = 0

        # for user_id in discord_user_ids:
        #     # asyncio.create_task(manage_roles(user_id))
        #     await manage_roles(user_id, guild, channel, role_to_add, role_to_remove)
        #     # await asyncio.sleep(0.1)
        
        for user_id in discord_user_ids:
            updates = await manage_roles(user_id, guild, channel, role_to_add, role_to_remove)
            updated += updates
            # await asyncio.sleep(0.1)
        
        logging.info(f"Total role updates performed: {updated}")
        
        logging.info("updated roles completed")
        sys.exit(0)
    else:
        logging.info("No user IDs provided for deletion.")

    cursor.close()
    db.close()


async def manage_roles(user_id, guild, channel, role_to_add, role_to_remove):

    try:
        member = await guild.fetch_member(user_id)
    except discord.NotFound:
        logging.info(f"Member {user_id} not found in guild")
        return 0
    except Exception as e:
        logging.error(f"Failed to fetch member {user_id}: {e}")
        return 0

    updates = 0


    async def retry_operation(operation, *args, max_retries=10, delay=1):
        for attempt in range(max_retries):
            try:
                await operation(*args)
                return True
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (2**attempt))
        return False

    if role_to_add and role_to_add not in member.roles:
        if await retry_operation(member.add_roles, role_to_add):
            updates += 1
            logging.info(
                f"User {member.name} ({user_id}) update: Added {role_to_add.name}"
            )
            # if await retry_operation(alert_user, user_id):
            #     updates += 1

    if role_to_remove and role_to_remove in member.roles:
        if await retry_operation(member.remove_roles, role_to_remove):
            logging.info(
                f"User {member.name} ({user_id}) update: Removed {role_to_remove.name}"
            )
            updates += 1

    return updates


@discord_connector.event
async def on_ready():
    global guild, channel
    logging.info(f"{discord_connector.user.name} has connected to Discord!")

    discord_user_ids = []
    with open("walletsToRemove.csv", "r") as file:
        csvreader = csv.DictReader(file)
        for row in csvreader:
            discord_user_ids.append(row["discordUserId"])

    sanitized_channel_name = sanitize_channel_name(channel_name)
    asyncio.create_task(delete_messages(discord_user_ids, sanitized_channel_name))


# discord_connector.run_bot() # removed for checking


def start_bot():
    discord_connector.run_bot()


if __name__ == "__main__":
    confirm = (
        input(
            "Are you sure you want to run the deletion script for DISCORD? (yes/no): "
        )
        .strip()
        .lower()
    )
    if confirm == "yes":
        confirm2 = (
            input(
                "Are you really sure you want to run the deletion script for DISCORD? (yes/no): "
            )
            .strip()
            .lower()
        )
        if confirm2 == "yes":
            asyncio.run(start_bot())
        else:
            logging.info("Script execution cancelled.")
    else:
        logging.info("Script execution cancelled.")
