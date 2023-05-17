import asyncio
import discord
from datetime import datetime
from init import discord_connector
from utils import database_query, update_reactions, remove_reactions


@discord_connector.event
async def on_ready():
    print(f'{discord_connector.user.name} connected')

@discord_connector.event
async def on_message(message):
    if message.author == discord_connector.user:
        return

    ref_id = message.reference.message_id if message.reference else None
    thread_id = message.channel.id if isinstance(message.channel, discord.Thread) else None
    message_type = 'replying_in_thread' if thread_id and ref_id else ('thread' if thread_id else ('reply' if ref_id else 'normal'))

    await database_query(
        "INSERT INTO discord (timestamp, user_id, username, discriminator, nick, message_id, content, channel, ref_id, thread_id, message_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (datetime.now(), message.author.id, message.author.name, message.author.discriminator, message.author.nick, message.id, message.content, message.channel.name, ref_id, thread_id, message_type)
    )

@discord_connector.event
async def on_message_edit(before, after):
    if before.author == discord_connector.user:
        return

    await database_query(
        "UPDATE discord SET content_edit = CONCAT(IFNULL(content_edit,''), %s) WHERE message_id = %s",
        (f"{datetime.now()}: {after.content}\n", before.id)
    )

@discord_connector.event
async def on_reaction_add(reaction, user):
    if user == discord_connector.user:
        return
    message = await reaction.message.channel.fetch_message(reaction.message.id)
    await update_reactions(reaction, user, message)

@discord_connector.event
async def on_reaction_remove(reaction, user):
    if user == discord_connector.user:
        return
    message = await reaction.message.channel.fetch_message(reaction.message.id)
    await remove_reactions(reaction, user, message)

@discord_connector.event
async def on_member_join(member):
    await database_query(
        "INSERT INTO members (id, name, discriminator, usernames) VALUES (%s, %s, %s, %s)",
        (member.id, member.name, member.discriminator, member.name)
    )

@discord_connector.event
async def on_member_update(before, after):
    if before.name != after.name:
        await database_query(
            "UPDATE members SET usernames = CONCAT(IFNULL(usernames,''), %s) WHERE id = %s",
            (f", {after.name}", after.id)
        )

if __name__ == "__main__":
    while True:
        try:
            discord_connector.run_bot()
        except discord.ConnectionClosed:
            continue
        break
