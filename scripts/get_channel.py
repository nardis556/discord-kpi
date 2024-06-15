import asyncio
import logging
from datetime import datetime, timedelta
from init import database_connector, discord_connector
import sys
# sys.path.append("/home/lars/code/discord-test") # local
sys.path.append("/home/lars/discord-kpi") # server
from config import channel_name, guild_id, role_id, remove_role_id_1, LOGGING_ENABLED, cooldown, alert_user_channel
import re


if LOGGING_ENABLED:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.disable(logging.CRITICAL)


def sanitize_channel_name(channel_name):
    """Sanitize the channel name to include only letters and numbers."""
    return ''.join(c for c in channel_name if c.isalnum())


def create_new_table(db, channel_name):
    sanitized_channel_name = sanitize_channel_name(channel_name)
    cursor = db.cursor()
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{sanitized_channel_name}` (
          `timestamp` timestamp NOT NULL,
          `user_id` bigint NOT NULL,
          `username` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
          `discriminator` smallint NOT NULL,
          `nick` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
          `message_id` bigint NOT NULL,
          `message_type` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
          `channel` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
          `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
          `content_edit` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
          `deleted` datetime DEFAULT NULL,
          `ref_id` bigint DEFAULT NULL,
          `thread_id` bigint DEFAULT NULL,
          `reactions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        cursor.execute(create_table_query)
        db.commit()
    except Exception as e:
        logging.info(f"An error occurred while creating the table: {e}")
    finally:
        cursor.close()

async def alert_user(user_id):
    try:
        channel = discord_connector.get_channel(alert_user_channel)
        print(channel)
        await channel.send(f"Congrats, <@{user_id}>! You've been whitelisted!")
    except Exception as e:
        return e

async def assign_role_to_user(user_id, guild_id, role_id):
    guild = discord_connector.get_guild(guild_id)
    if not guild:
        logging.info(f"Guild with ID {guild_id} not found.")
        return

    try:
        member = await guild.fetch_member(user_id)
    except:
        logging.info(f"Member with ID {user_id} not found in guild {guild_id}.")
        return

    set_role = guild.get_role(role_id)
    if not set_role:
        logging.info(f"Role with ID {role_id} not found in guild {guild_id}.")
        return
    
    remove_role_1 = guild.get_role(remove_role_id_1)
    if not remove_role_1:
        logging.info(f"Role with ID {remove_role_id_1} not found in guild {remove_role_id_1}.")
        return

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

    if await retry_operation(member.add_roles, set_role):
        logging.info(f"Role {set_role.name} added to user {member.name}.")

    if await retry_operation(member.remove_roles, remove_role_1):
        logging.info(f"Role {remove_role_1.name} removed from user {member.name}.")

    # if not (user_id == 111244106990153728 or user_id == "111244106990153728"):
    await retry_operation(alert_user, user_id)


def extract_valid_ethereum_address(text):
    pattern = r'0x[a-fA-F0-9]{40}'
    matches = re.findall(pattern, text)
    for address in matches:
        if is_valid_ethereum_address(address):
            return address
    return None


def is_valid_ethereum_address(address):
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return re.match(pattern, address) is not None


async def insert_records_into_new_table(records, channel_name, cursor, guild_id, role_id):
    sanitized_channel_name = sanitize_channel_name(channel_name)
    for record in records:
        user_id = record[1]
        content = record[8]

        valid_address = extract_valid_ethereum_address(content)
        if valid_address:
            logging.info(f"Valid Ethereum address found in content: {valid_address}")
            cursor.execute(f"SELECT COUNT(*) FROM `{sanitized_channel_name}` WHERE `user_id` = %s", (user_id,))
            if cursor.fetchone()[0] == 0:
                insert_query = f"INSERT INTO `{sanitized_channel_name}` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                record_values = list(record)
                record_values[8] = valid_address
                cursor.execute(insert_query, tuple(record_values))
                await assign_role_to_user(user_id, guild_id, role_id)
            else:
                logging.info(f"User ID {user_id} already exists in '{sanitized_channel_name}', skipping insertion.")
        else:
            logging.info(f"No valid Ethereum address found in content: {content}, skipping insertion.")
    cursor.close()


async def gather_channel_data(channel_name, guild_id, role_id):
    last_entry_date = None
    while True:
        logging.info('Starting script')
        db = database_connector.connect()
        cursor = db.cursor()
        sanitized_channel_name = sanitize_channel_name(channel_name)
        logging.info(sanitized_channel_name)

        try:
            create_new_table(db, sanitized_channel_name)
            if last_entry_date is None:
                cursor.execute(f"SELECT MAX(timestamp) FROM `{sanitized_channel_name}`")
                last_entry_date = cursor.fetchone()[0]

            if last_entry_date is None:
                last_entry_date = datetime.now() - timedelta(days=1)
                logging.info(f"No previous data found. Starting from 24 hours ago: {last_entry_date}")

            current_time = datetime.now()
            last_entry_date -= timedelta(minutes=5)

            select_query = f"""
                SELECT *
                FROM discord
                WHERE channel = %s AND timestamp > %s AND timestamp <= %s
            """
            cursor.execute(select_query, (channel_name, last_entry_date, current_time))
            records = cursor.fetchall()

            if records:
                logging.info(f"Inserting {len(records)} new records into {sanitized_channel_name}.")
                await insert_records_into_new_table(records, sanitized_channel_name, cursor, guild_id, role_id)
                last_entry_date = records[-1][0]
            else:
                logging.info(f"No new records found to insert into {sanitized_channel_name}.")

            db.commit()

        except Exception as e:
            db.rollback()
            logging.error(f"Error: {e}")

        finally:
            cursor.close()
            db.close()

        logging.info(f'Sleeping for {cooldown} seconds')
        await asyncio.sleep(cooldown)


@discord_connector.event
async def on_ready():
    logging.info(f'{discord_connector.user.name} has connected to Discord!')
    asyncio.create_task(gather_channel_data(channel_name, guild_id, role_id))

discord_connector.run_bot()
