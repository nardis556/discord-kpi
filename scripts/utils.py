from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import discord
import re
from init import database_connector, discord_connector



@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def database_query(query, values=None):
    # print('database_query')
    db = database_connector.connect()
    cursor = db.cursor()
    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)
    db.commit()
    db.close()




async def parse_reactions(reactions):
    # print('parse_reactions')
    reactions_dict = {}
    if reactions:
        reactions_list = reactions.split(', ')
        for reaction_str in reactions_list:
            emoji, count = reaction_str.split(':')
            match = re.match(r'<a?:?(.+?):\d+>', emoji)
            if match:
                emoji = match.group(1)
            reactions_dict[emoji] = int(count)
    return reactions_dict



async def parse_content(message, discord_connector):
    # print('parse_content')
    content = message.content
    user_mentions = re.findall(r'<@(\d+)>', content)
    for user_id in user_mentions:
        user = await discord_connector.fetch_user(int(user_id))
        content = content.replace(f'<@{user_id}>', f'@{user.name}#{user.discriminator}')

    # if message.stickers:
    #     sticker_details = ', '.join([f'STICKER: {sticker.name}' for sticker in message.stickers])
    #     content = f'{content}\n{sticker_details}'

    content = re.sub(r'<a?:([^:]+):\d+>', r'EMOJI: \1', content)

    if message.attachments:
        image_urls = ', '.join([f'IMAGE: {attachment.url}' for attachment in message.attachments])
        if not content:
            content = f'{image_urls}'
        else:
            content = f'{content}\n{image_urls}'

    return content



async def update_reactions(reaction, user, message, on_message):
    db = database_connector.connect()
    cursor = db.cursor()
    cursor.execute("SELECT reactions FROM discord WHERE message_id = %s", (message.id,))
    result = cursor.fetchone()
    db.close()

    if not result and message.author != discord_connector.user:
        await on_message(message)

    updated_reactions = {}

    reactions = message.reactions

    for reaction in reactions:
        emoji = str(reaction.emoji)
        if emoji.startswith('<:'):
            emoji = emoji.split(':')[1]
        elif emoji.startswith('<a:'):
            emoji = emoji.split(':')[1]
        updated_reactions[emoji] = reaction.count

    updated_reactions_str = ', '.join(f'{emoji}:{count}' for emoji, count in updated_reactions.items())

    await database_query(
        "UPDATE discord SET reactions = %s WHERE message_id = %s",
        (updated_reactions_str, message.id)
    )



async def update_message(message):
    db = database_connector.connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM discord WHERE message_id = %s", (message.id,))
    result = cursor.fetchone()
    db.close()

    nick = message.author.nick if isinstance(message.author, discord.Member) else None

    content = await parse_content(message, discord_connector)
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
        "UPDATE discord SET content = %s WHERE message_id = %s",
        (content, message.id)
    )
