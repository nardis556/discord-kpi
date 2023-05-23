import asyncio
import discord
from datetime import datetime, timedelta
import traceback
import re
from init import discord_connector, database_connector
from utils import database_query, update_reactions, parse_content, message_id_selector, get_type_of_message


@discord_connector.event
async def on_ready():
    print(f'{discord_connector.user.name} connected')
    for guild in discord_connector.guilds:
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.permissions_for(guild.me).read_messages:
                    await fetch_recent_messages(channel)
                    await add_all_members()


async def fetch_recent_messages(channel):
    now = datetime.utcnow()
    limit_time = now - timedelta(hours=2)

    async for message in channel.history(limit=None, after=limit_time):

        result = await message_id_selector(message)

        if not result:
            await on_message(message)
        else:
            await on_message_edit(result[2], message)

        for reaction in message.reactions:
            user = type('User', (object,), {'id': 'unknown'})
            await update_reactions(reaction, user, message, on_message)


@discord_connector.event
async def on_message_edit(before_content, after_message):
    if after_message.author == discord_connector.user:
        return
    
    result = await message_id_selector(after_message)

    if not result or result[2] == after_message.content:
        return

    await database_query(
        "UPDATE discord SET content_edit = CONCAT(IFNULL(content_edit,''), %s) WHERE message_id = %s",
        (f"{after_message.content}\n", after_message.id)
    )

@discord_connector.event
async def on_message(message):
    if message.author == discord_connector.user:
        return

    ref_id = message.reference.message_id if message.reference else None
    thread_id = message.channel.id if isinstance(message.channel, discord.Thread) else None

    message_type = get_type_of_message(ref_id, thread_id)

    nick = message.author.nick if isinstance(message.author, discord.Member) else None

    content = await parse_content(message, discord_connector)

    content = re.sub(r'<a?:([^:]+):\d+>', r'EMOJI: \1', content)

    await database_query(
        "INSERT INTO discord (timestamp, user_id, username, discriminator, nick, message_id, content, channel, ref_id, thread_id, message_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (datetime.now(), message.author.id, message.author.name, message.author.discriminator, nick, message.id, content, message.channel.name, ref_id, thread_id, message_type)
    )


@discord_connector.event
async def on_message_delete(message):
    await database_query(
        "UPDATE discord SET deleted = %s WHERE message_id = %s",
        (datetime.now(), message.id)
    )


@discord_connector.event
async def on_reaction_add(reaction, user):
    message = await reaction.message.channel.fetch_message(reaction.message.id)
    await update_reactions(reaction, user, message, on_message)


@discord_connector.event
async def on_reaction_remove(reaction, user):
    message = await reaction.message.channel.fetch_message(reaction.message.id)
    await update_reactions(reaction, user, message, on_message)


@discord_connector.event
async def on_member_join(member):
    timestamp = datetime.now()
    user_info = f"{member.id}: {member.name} #{member.discriminator}"
    in_server = True
    await database_query(
        "INSERT INTO followers (timestamp, user_info, in_server) VALUES (%s, %s, %s)",
        (timestamp, user_info, in_server)
    )

@discord_connector.event
async def on_member_remove(member):
    timestamp = datetime.now()
    user_info = f"{member.id}: {member.name} #{member.discriminator}"
    in_server = False
    await database_query(
        "UPDATE followers SET timestamp = %s, in_server = %s WHERE user_info = %s",
        (timestamp, in_server, user_info)
    )


async def add_all_members():
    for guild in discord_connector.guilds:
        last_member = await database_query(
            "SELECT user_info FROM followers ORDER BY user_info DESC LIMIT 1",
            fetch=True
        )
        last_member_id = None
        if last_member:
            last_member_id = int(last_member[0].split(":")[0])

        # goat_role = discord.utils.get(guild.roles, name='GOAT')

        async for member in guild.fetch_members(limit=1000):
            if last_member_id and member.id <= last_member_id:
                continue

            # if goat_role in member.roles:
            timestamp = datetime.now()
            user_info = f"{member.id}: {member.name} #{member.discriminator}"
            in_server = True

            existing_user = await database_query(
                "SELECT * FROM followers WHERE user_info = %s",
                (user_info,),
                fetch=True
            )
            if not existing_user:
                await database_query(
                    "INSERT INTO followers (timestamp, user_info, in_server) VALUES (%s, %s, %s)",
                    (timestamp, user_info, in_server)
                )



if __name__ == "__main__":
    while True:
        try:
            discord_connector.run_bot()
        except discord.ConnectionClosed:
            traceback.print_exc()
            continue
        break
