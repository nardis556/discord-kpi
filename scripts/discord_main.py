import asyncio
import discord
from datetime import datetime, timedelta
import traceback
import requests
import re
from init import discord_connector, database_connector
from utils import database_query, update_reactions, parse_content, message_id_selector, get_type_of_message
import sys
sys.path.append("/home/lars/discord-kpi")
from config import slack_webhook_url
import json

identifier = 'main'

loopi = 0
connecti = 0
disconnecti = 0
reconnect = 0
shard_ready = 0
shard_resumed = 0

def send_to_slack(message):
    response = requests.post(
        slack_webhook_url,
        data=json.dumps({'text': message}),
        headers={'Content-Type': 'application/json'}
    )
    return response

from datetime import datetime

def get_current_time_formatted() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@discord_connector.event
async def on_shard_connect(shard_id):
    send_to_slack(f'{get_current_time_formatted()} connected to shard {shard_id}')

@discord_connector.event
async def on_shard_disconnect(shard_id):
    send_to_slack(f'{get_current_time_formatted()} disconnected to shard {shard_id}')


@discord_connector.event
async def on_connect():
    global connecti
    connecti += 1
    send_to_slack(f'{get_current_time_formatted()} {identifier} connected. Connect count: {connecti}')
    # NEW
    for guild in discord_connector.guilds:
        # print(discord_connector.guilds)
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.permissions_for(guild.me).read_messages:
                    await fetch_recent_messages(channel, 2)
                    # await add_all_members()

@discord_connector.event
async def on_shard_ready(shard_id):
    global shard_ready 
    shard_ready += 1
    send_to_slack(f'{get_current_time_formatted()} {identifier} shard ready: {shard_id}')

@discord_connector.event
async def on_shard_resumed(shard_id):
    global shard_resumed
    shard_resumed += 1
    send_to_slack(f'{get_current_time_formatted()} {identifier} shard resumed: {shard_id}')

@discord_connector.event
async def on_ready():
    send_to_slack(f'{get_current_time_formatted()} {identifier} bot is ready.')
    print(f'{discord_connector.user.name} connected')
    for guild in discord_connector.guilds:
        # print(discord_connector.guilds)
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.permissions_for(guild.me).read_messages:
                    await fetch_recent_messages(channel, 2)
                    # await add_all_members()

@discord_connector.event
async def on_resumed():
    print(f'{discord_connector.user.name} reconnected')
    send_to_slack(f'{get_current_time_formatted()} {identifier} reconnected.')
    for guild in discord_connector.guilds:
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.permissions_for(guild.me).read_messages:
                    await fetch_recent_messages(channel, 0.5)

async def fetch_recent_messages(channel, fetch_from_hours_ago):
    now = datetime.utcnow()
    limit_time = now - timedelta(hours=fetch_from_hours_ago)

    async for message in channel.history(limit=None, after=limit_time):

        result = await message_id_selector(message)

        if not result:
            await on_message(message)
        else:
            content = await parse_content(message, discord_connector)
            if result[8] != content:
                await on_message_edit(result[8], message ,content)

        for reaction in message.reactions:
            user = type('User', (object,), {'id': 'unknown'})
            await update_reactions(reaction, user, message, on_message)

@discord_connector.event
async def on_message_edit(before_content, after_message, parsed_content=False):
    if after_message.author == discord_connector.user:
        return
    if not parsed_content:
        parsed_content = await parse_content(after_message, discord_connector=False)

    result = await message_id_selector(after_message)

    if not result or result[2] == after_message.content:
        return

    await database_query(
        "UPDATE discord SET content_edit = CONCAT(IFNULL(content_edit,''), %s) WHERE message_id = %s",
        (f"{parsed_content}\n", after_message.id)
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
        (datetime.now(), message.author.id, message.author.name, message.author.discriminator, nick, message.id, content, message.channel.name, ref_id, thread_id, message_type),
        update=True
    )

#         # test
#     if message.content.startswith('!test') and message.author.id == 111244106990153728:
#         try:
#             _, num_cycles = message.content.split()
#             await test(message, num_cycles)
#         except ValueError:
#             print("Please provide a valid number for num_cycles.")

# async def test(message, num_cycles):
#     num_cycles = int(num_cycles)
#     for i in range(num_cycles):
#         await message.channel.send(f'test1 {i}')

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
        "INSERT INTO members (timestamp, user_info, in_server) VALUES (%s, %s, %s)",
        (timestamp, user_info, in_server)
    )

@discord_connector.event
async def on_member_remove(member):
    timestamp = datetime.now()
    user_info = f"{member.id}: {member.name} #{member.discriminator}"
    in_server = False
    await database_query(
        "UPDATE members SET timestamp = %s, in_server = %s WHERE user_info = %s",
        (timestamp, in_server, user_info)
    )

@discord_connector.event
async def on_disconnect():
    global disconnecti
    disconnecti += 1
    send_to_slack(f'{get_current_time_formatted()} {identifier} bot disconnected. Disconnect count {disconnecti}')

if __name__ == "__main__":
    while True:
        try:
            loopi += 1
            send_to_slack(f'{get_current_time_formatted()} main loop started. Loop count {loopi}')
            discord_connector.run_bot()
        except discord.ConnectionClosed:
            send_to_slack(f'Error on main {traceback.print_exc()}')
            traceback.print_exc()
            continue
        break
