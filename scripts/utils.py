from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from init import database_connector, discord_connector

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def database_query(query, values=None):
    db = database_connector.connect()
    cursor = db.cursor()
    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)
    db.commit()
    db.close()

async def parse_reactions(reactions):
    reactions_dict = {}
    if reactions:
        reactions_list = reactions.split(', ')
        for reaction_str in reactions_list:
            emoji, count = reaction_str.split(':')
            reactions_dict[emoji] = int(count)
    return reactions_dict

async def update_reactions(reaction, user, message, on_message):
    db = database_connector.connect()
    cursor = db.cursor()
    cursor.execute("SELECT reactions FROM discord WHERE message_id = %s", (message.id,))
    result = cursor.fetchone()
    db.close()

    if not result and message.author != discord_connector.user:
        await on_message(message)

    reactions_dict = await parse_reactions(result[0])

    emoji = str(reaction.emoji)
    if emoji in reactions_dict:
        reactions_dict[emoji] += 1
    else:
        reactions_dict[emoji] = 1

    reactions_str = ', '.join(f'{emoji}:{count}' for emoji, count in reactions_dict.items())

    await database_query(
        "UPDATE discord SET reactions = %s WHERE message_id = %s",
        (reactions_str, message.id)
    )

async def remove_reactions(reaction, user, message, on_message):
    db = database_connector.connect()
    cursor = db.cursor()
    cursor.execute("SELECT reactions FROM discord WHERE message_id = %s", (message.id,))
    result = cursor.fetchone()
    db.close()

    if not result and message.author != discord_connector.user:
        await on_message(message)

    reactions_dict = await parse_reactions(result[0])

    emoji = str(reaction.emoji)
    if emoji in reactions_dict:
        reactions_dict[emoji] -= 1
        if reactions_dict[emoji] <= 0:
            del reactions_dict[emoji]
    else:
        return

    reactions_str = ', '.join(f'{emoji}:{count}' for emoji, count in reactions_dict.items())

    await database_query(
        "UPDATE discord SET reactions = %s WHERE message_id = %s",
        (reactions_str, message.id)
    )
