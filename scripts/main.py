import asyncio
import discord
from datetime import datetime
import traceback
import re
from init import discord_connector
from utils import database_query, update_reactions, remove_reactions

@discord_connector.event
async def on_ready():
    print(f'{discord_connector.user.name} connected')

@discord_connector.event
async def on_message(message):
    print('on_message')
    if message.author == discord_connector.user:
        return

    ref_id = message.reference.message_id if message.reference else None
    thread_id = message.channel.id if isinstance(message.channel, discord.Thread) else None
    message_type = 'replying_in_thread' if thread_id and ref_id else ('thread' if thread_id else ('reply' if ref_id else 'original'))

    nick = message.author.nick if isinstance(message.author, discord.Member) else None

    content = message.content
    if message.stickers:
        sticker_details = ', '.join([f'STICKER: {sticker.name}' for sticker in message.stickers])
        content = f'{content}\n{sticker_details}'

    content = re.sub(r'<a?:([^:]+):\d+>', r'EMOJI: \1', content)

    if message.attachments:
        image_urls = ', '.join([f'IMAGE: {attachment.url}' for attachment in message.attachments])
        if not content:
            content = f'{image_urls}'
        else:
            content = f'{content}\n{image_urls}'

    await database_query(
        "INSERT INTO discord (timestamp, user_id, username, discriminator, nick, message_id, content, channel, ref_id, thread_id, message_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (datetime.now(), message.author.id, message.author.name, message.author.discriminator, nick, message.id, content, message.channel.name, ref_id, thread_id, message_type)
    )


@discord_connector.event
async def on_message_delete(message):
    print('on_message_delete')
    await database_query(
        "UPDATE discord SET deleted = %s WHERE message_id = %s",
        (datetime.now(), message.id)
    )

@discord_connector.event
async def on_message_edit(before, after):
    print('on_message_edit')
    if before.author == discord_connector.user:
        return

    await database_query(
        "UPDATE discord SET content_edit = CONCAT(IFNULL(content_edit,''), %s) WHERE message_id = %s",
        (f"{datetime.now()}: {after.content}\n", before.id)
    )

@discord_connector.event
async def on_reaction_add(reaction, user):
    print('on_reaction_add')
    message = await reaction.message.channel.fetch_message(reaction.message.id)
    await update_reactions(reaction, user, message, on_message)


@discord_connector.event
async def on_reaction_remove(reaction, user):
    print('on_reaction_remove')
    message = await reaction.message.channel.fetch_message(reaction.message.id)
    await remove_reactions(reaction, user, message, on_message)

@discord_connector.event
async def on_member_join(member):
    await database_query(
        "INSERT INTO members (id, name, discriminator, usernames) VALUES (%s, %s, %s, %s)",
        (member.id, member.name, member.discriminator, member.name)
    )

@discord_connector.event
async def on_member_update(before, after):
    print('on_member_update')
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
            traceback.print_exc()
            continue
        break
